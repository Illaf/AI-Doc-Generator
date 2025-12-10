import os
import tempfile
import shutil
import asyncio,uuid
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse,FileResponse
from pydantic import BaseModel, Field
import git
import ollama
import ast
from fastapi import APIRouter
from requests import Session
from services.export_doc import export_document
from services.themes import build_prompt
from services.caching import SessionLocal, get_cached_doc,save_cached_doc,get_commit_hash,STORAGE_ROOT,sanitize_filename,get_db
router = APIRouter()

# app = FastAPI(title="OptimizedDocGenerator", version="2.0")


# ============================================================================
# CONFIGURATION
# ============================================================================

SKIP_PATTERNS = {
    "dirs": {
        ".git", ".github", ".gitlab", ".vscode", ".idea", "__pycache__",
        "node_modules", ".pytest_cache", ".mypy_cache", ".tox", "dist",
        "build", "venv", ".venv", "env", "site-packages", "vendor",
        ".eggs", "htmlcov", "migrations"
    },
    "files": {"__init__.py", "setup.py", "conftest.py"},
    "prefixes": ("test_", ".", "_"),
    "suffixes": (".pyc", ".pyo", ".pyd", ".so", ".dll")
}
job_store={}


SYSTEM_PROMPT = """You are an expert technical writer. Create concise, clear documentation 
for non-technical users. Focus on WHAT the code does and WHY it exists, not HOW.
Keep responses under 150 words. Use simple language and analogies."""


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class FileInfo:
    """Represents a processed file with its content"""
    path: str
    content: str
    size: int
    
class GenerateRequest(BaseModel):
    repo_url: str
    branch: str = Field(default="master")
    access_token: Optional[str] = None
    model: str = "llama3.2"
    max_workers: int = 10
    stream: bool = False
    format: str = "md"
    theme: Optional[str] = None


@router.post("/start-generation")
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = uuid.uuid4().hex

    job_store[job_id] = {
        "status": "queued",
        "progress": 0,
        "output_file": None,
        "error": None,
    }

    # START PURE WORKER
    background_tasks.add_task(worker_generate_docs, job_id, req)

    return {"job_id": job_id, "status": "started"}

# ============================================================================
# UTILITIES
# ============================================================================

def should_skip(path: Path) -> bool:
    """Fast path filtering using set lookups"""
    # Check parents for skip directories
    if any(p.name in SKIP_PATTERNS["dirs"] for p in path.parents):
        print(f"Skipped (dir): {path}")
        return True
    
    # Check filename
    name = path.name
    if name in SKIP_PATTERNS["files"]:
        print(f"Skipped (file): {name}")
        return True
    
    # Check prefixes and suffixes
    if name.startswith(SKIP_PATTERNS["prefixes"]) or name.endswith(SKIP_PATTERNS["suffixes"]):
        print(f"Skipped (dir): {name}")
        return True
    
    return False


def safe_rmtree(path: str):
    """Cross-platform safe directory removal"""
    def on_error(func, p, exc):
        os.chmod(p, 0o777)
        func(p)
    
    if os.path.exists(path):
        shutil.rmtree(path, onerror=on_error)


def clone_repository(url: str, branch: str, token: Optional[str], dest: str) -> git.Repo:
    """Clone repository with authentication support"""
    if token and url.startswith("https://"):
        url = url.replace("https://", f"https://{token}@")
    
    return git.Repo.clone_from(
        url, dest, branch=branch, depth=1,
        single_branch=True,  # Only clone target branch
        allow_unsafe_options=True,
        config='core.autocrlf=false'  # Faster on Windows
    )


# ============================================================================
# CODE ANALYSIS
# ============================================================================

def analyze_file(file_path: Path) -> Optional[str]:
    """Extract meaningful code structure efficiently"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        
        # Quick size check - skip very large or empty files
        if len(content) < 10 or len(content) > 100_000:
            return None
        
        tree = ast.parse(content)
        elements = []
        
        # Module docstring
        if doc := ast.get_docstring(tree):
            elements.append(f"MODULE: {doc[:200]}")
        
        # Classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or "No description"
                elements.append(f"CLASS {node.name}: {doc[:150]}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):  # Skip private functions
                    doc = ast.get_docstring(node) or "No description"
                    elements.append(f"FUNCTION {node.name}: {doc[:150]}")
        
        return "\n".join(elements) if elements else None
        
    except Exception:
        return None

print("STORAGE_ROOT:", STORAGE_ROOT, type(STORAGE_ROOT))

# ============================================================================
# LLM INTERACTION
# ============================================================================

def generate_documentation(file_info: FileInfo, model: str,theme:str) -> Optional[Dict[str, str]]:
    """Generate documentation for a single file"""
    if not file_info.content:
        return None
    user_prompt=build_prompt(file_info.content,theme)
#     user_prompt = f"""File: {file_info.path}

# Structure:
# {file_info.content}

# Explain this file's purpose and key functionality in simple terms."""

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                
            ],
            
            options={
                "temperature": 0.3,  # More consistent output
                "num_predict": 200,  # Limit response length
            },
            stream= True
        )
        full_text = ""
        for chunk in response:
            if "message" in chunk and "content" in chunk["message"]:
                full_text += chunk["message"]["content"]

        return {
            "path": file_info.path,
            "documentation": full_text.strip()
        }
    except Exception as e:
        print(f"Error generating docs for {file_info.path}: {e}")
        return None


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_repository(repo_path: Path, model: str, max_workers: int,theme: str) -> List[Dict[str, str]]:
    """Process all files in parallel with optimal batching"""
    
    # Stage 1: Fast file discovery and filtering
    py_files = [f for f in repo_path.rglob("*.py") if not should_skip(f)]
    
    if not py_files:
        return []
    
    # Stage 2: Parallel code analysis
    file_infos: List[FileInfo] = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(analyze_file, f): f for f in py_files
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                content = future.result()
                if content:
                    file_infos.append(FileInfo(
                        path=str(file_path.relative_to(repo_path)),
                        content=content,
                        size=len(content)
                    ))
            except Exception:
                continue
    
    if not file_infos:
        return []
    
    # Sort by size (process smaller files first for better UX)
    file_infos.sort(key=lambda x: x.size)
    
    # Stage 3: Parallel LLM documentation generation
    results = []
    
    with ThreadPoolExecutor(max_workers=min(max_workers, 5)) as executor:
        future_to_info = {
            executor.submit(generate_documentation, info, model, theme): info 
            for info in file_infos
        }
        
        for future in as_completed(future_to_info):
            try:
                if result := future.result():
                    results.append(result)
            except Exception:
                continue
    
    return results


# ============================================================================
# API ENDPOINTS
# ============================================================================

def worker_generate_docs(job_id: str, req: GenerateRequest):
    db = SessionLocal()
    tmp_dir = tempfile.mkdtemp(prefix="repo-")

    try:
        job_store[job_id]["status"] = "Cloning repository"
        job_store[job_id]["progress"] = 10

        repo = clone_repository(req.repo_url, req.branch, req.access_token, tmp_dir)
        repo.git.clear_cache()
        repo.close()

        repo_path = Path(tmp_dir)

        # Commit hash
        commit_hash = get_commit_hash(repo_path)

        # Check cache
        cached = get_cached_doc(db, req.repo_url, req.branch, commit_hash)
        if cached:
            job_store[job_id]["status"] = "Loaded from cache"
            job_store[job_id]["progress"] = 100
            job_store[job_id]["output_file"] = cached.file_path
            return

        # Process files
        job_store[job_id]["status"] = "Processing files"
        job_store[job_id]["progress"] = 30

        results = process_repository(repo_path, req.model, req.max_workers, req.theme)

        if not results:
            job_store[job_id]["error"] = "No documentable Python files found"
            job_store[job_id]["status"] = "Failed"
            return

        # Build markdown
        job_store[job_id]["status"] = "Building Markdown"
        job_store[job_id]["progress"] = 50

        docs = ["# Repository Documentation\n"]
        for item in results:
            docs.append(f"## `{item['path']}`\n\n{item['documentation']}\n")

        final_doc = "\n".join(docs)

        # Export
        job_store[job_id]["status"] = "Exporting document"
        job_store[job_id]["progress"] = 80

        output_file = export_document(final_doc, req.format)

        # cache folder
        folder = STORAGE_ROOT / sanitize_filename(req.repo_url) / commit_hash
        folder.mkdir(parents=True, exist_ok=True)

        final_path = folder / f"documentation.{req.format}"
        shutil.move(output_file, final_path)

        # store cache
        save_cached_doc(
            db,
            repo_url=req.repo_url,
            branch=req.branch,
            commit_hash=commit_hash,
            doc_path=str(final_path),
        )

        job_store[job_id]["status"] = "Completed"
        job_store[job_id]["progress"] = 100
        job_store[job_id]["output_file"] = str(final_path)

    except Exception as e:
        job_store[job_id]["error"] = str(e)
        job_store[job_id]["status"] = "Failed"

    finally:
        safe_rmtree(tmp_dir)
        db.close()




@router.get("/health")
def health():
    """Health check endpoint"""
    try:
        ollama.list()  # Check if Ollama is running
        return {"status": "healthy", "ollama": "connected"}
    except Exception:
        return {"status": "degraded", "ollama": "disconnected"}

@router.get("/status/{job_id}")
def get_status(job_id:str):
    if job_id not in job_store:
        return HTTPException(404,"Invalid Job Id") 
    return job_store[job_id]

@router.get("/download/{job_id}")
def download(job_id: str):
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(404, "Invalid job_id")

    if job["error"]:
        raise HTTPException(500, job["error"])

    if job["status"] != "Completed":
        return {"status": job["status"], "progress": job["progress"]}

    return FileResponse(job["output_file"])



@router.get("/")
def root():
    """API information"""
    return {
        "service": "Optimized Documentation Generator",
        "version": "2.0",
        "endpoints": {
            "generate": "/generate-docs",
            "health": "/health"
        }
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         log_level="info"
#     )