import os
import tempfile, time
import shutil
import urllib.parse
import asyncio, uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from utils.list_branches import list_remote_branches, branch_exists
import git
import ollama
from fastapi import APIRouter
from services.export_doc import export_document
from services.themes import build_prompt
from services.caching import SessionLocal, get_cached_doc, save_cached_doc, get_commit_hash, STORAGE_ROOT, sanitize_filename, get_db

router = APIRouter()

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

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
job_store = {}

BATCH_SIZE = 8
MAX_BATCH_TOKENS = 12000
MAX_PARALLEL_BATCHES = 2

SYSTEM_PROMPT = """You are an expert technical writer. Create concise, clear documentation 
for non-technical users. Focus on WHAT the code does and WHY it exists, not HOW.
Keep each file's documentation under 150 words. Use simple language and analogies."""


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class FileInfo:
    """Represents a processed file with its content"""
    path: str
    content: str
    size: int
    importance_score: int = 0


class GenerateRequest(BaseModel):
    repo_url: str
    branch: str = Field(default="master")
    access_token: Optional[str] = None
    model: str = "llama3.2"
    max_workers: int = 2
    stream: bool = False
    format: str = "md"
    theme: Optional[str] = None
    use_cache: bool = Field(default=True, description="Use cached documentation if available")
    template: str = Field(default="minimal", description="UI template for HTML/PDF output") 


class BranchRequest(BaseModel):
    repo_url: str
    access_token: Optional[str] = None


@router.post("/start-generation")
def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = uuid.uuid4().hex
    print("use_cache =", req.use_cache)
    job_store[job_id] = {
        "status": "queued",
        "progress": 0,
        "output_file": None,
        "error": None,
        "total_batches": 0,
        "completed_batches": 0,
    }

    background_tasks.add_task(worker_generate_docs, job_id, req)

    return {"job_id": job_id, "status": "started"}


# ============================================================================
# UTILITIES
# ============================================================================

def parse_github_url(url: str) -> Tuple[str, Optional[str]]:
    """
    Parse GitHub URL to extract base repo URL and subdirectory path.
    
    Examples:
        'https://github.com/user/repo' -> ('https://github.com/user/repo', None)
        'https://github.com/user/repo.git' -> ('https://github.com/user/repo', None)
        'https://github.com/user/repo/tree/main/subfolder' -> ('https://github.com/user/repo', 'subfolder')
        'https://github.com/user/repo/tree/main/Address%20Validator' -> ('https://github.com/user/repo', 'Address Validator')
    """
    # Remove trailing slashes and .git suffix
    url = url.rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    
    print(f"🔍 Parsing URL: {url}")
    
    # Check if URL contains '/tree/{branch}/'
    if '/tree/' in url:
        parts = url.split('/tree/')
        base_url = parts[0]
        
        # Extract subdirectory path (after branch name)
        if len(parts) > 1:
            tree_parts = parts[1].split('/', 1)
            if len(tree_parts) > 1:
                # URL decode the subdirectory name (handles %20 etc.)
                subdir = urllib.parse.unquote(tree_parts[1])
                print(f"✅ Extracted - Base: {base_url}, Subdir: {subdir}")
                return base_url, subdir
    
    print(f"✅ No subdirectory found - Base: {url}")
    return url, None


def should_skip(path: Path) -> bool:
    """Fast path filtering using set lookups"""
    if any(p.name in SKIP_PATTERNS["dirs"] for p in path.parents):
        return True

    name = path.name
    if name in SKIP_PATTERNS["files"]:
        return True

    if name.startswith(SKIP_PATTERNS["prefixes"]) or name.endswith(SKIP_PATTERNS["suffixes"]):
        return True

    return False


def calculate_importance(file_path: Path, content: str) -> int:
    """Score file importance (higher = more important)"""
    score = 0

    parts = file_path.parts
    if "core" in parts or "main" in parts or "api" in parts:
        score += 5
    if len(parts) <= 3:
        score += 3

    if "class " in content.lower():
        score += 2
    if "def " in content:
        score += 1
    if len(content.split("\n")) > 50:
        score += 2

    return score


def safe_rmtree(path: str, retries=5):
    for i in range(retries):
        try:
            shutil.rmtree(path, ignore_errors=False)
            return
        except PermissionError:
            time.sleep(1)
    shutil.rmtree(path, ignore_errors=True)


def clone_repository(url: str, branch: str, token: Optional[str], dest: str) -> Tuple[git.Repo, Optional[str]]:
    """
    Clone repository with sparse checkout for subdirectories.
    Returns (repo, subdirectory_path)
    """
    base_url, subdir = parse_github_url(url)
    
    if token and base_url.startswith("https://"):
        clone_url = base_url.replace("https://", f"https://{token}@")
    else:
        clone_url = base_url

    print(f"🔗 Base URL: {base_url}")
    if subdir:
        print(f"📁 Subdirectory: {subdir}")

    # Always use sparse checkout approach for better control
    if os.path.exists(dest):
        safe_rmtree(dest)
    
    os.makedirs(dest, exist_ok=True)
    
    try:
        # Initialize repo
        repo = git.Repo.init(dest)
        origin = repo.create_remote('origin', clone_url)
        
        # Configure Git settings
        repo.git.config('core.protectNTFS', 'false')
        repo.git.config('core.protectHFS', 'false')
        repo.git.config('core.autocrlf', 'false')
        
        if subdir:
            # Enable sparse checkout
            repo.git.config('core.sparseCheckout', 'true')
            repo.git.config('core.sparseCheckoutCone', 'false')
            
            # Create sparse-checkout file
            sparse_file = os.path.join(dest, '.git', 'info', 'sparse-checkout')
            os.makedirs(os.path.dirname(sparse_file), exist_ok=True)
            
            with open(sparse_file, 'w') as f:
                # Only checkout the subdirectory
                f.write(f'{subdir}/\n')
                # Exclude media files
                f.write('!*.jpg\n')
                f.write('!*.png\n')
                f.write('!*.gif\n')
                f.write('!*.mp4\n')
                f.write('!*.zip\n')
            
            print(f"⚙️ Sparse checkout configured for: {subdir}")
        
        # Fetch the branch
        print(f"📥 Fetching branch: {branch}")
        origin.fetch(branch, depth=1)
        
        # Checkout
        print(f"✅ Checking out files")
        repo.git.checkout(f'origin/{branch}')
        
        # Verify the subdirectory exists in working tree
        if subdir:
            subdir_path = Path(dest) / subdir
            if not subdir_path.exists():
                raise Exception(f"Subdirectory '{subdir}' not found after checkout")
            print(f"✅ Subdirectory verified: {subdir_path}")
        
        return repo, subdir
        
    except Exception as e:
        print(f"❌ Clone error: {e}")
        # Cleanup on failure
        if os.path.exists(dest):
            safe_rmtree(dest)
        raise


def analyze_file(file_path: Path) -> Optional[str]:
    """Fast extraction of key code elements"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if len(content) < 10 or len(content) > 100_000:
            return None

        lines = content.split("\n")
        elements = []

        in_docstring = False
        docstring_content = []

        for i, line in enumerate(lines[:100]):
            stripped = line.strip()

            if i < 5 and ('"""' in stripped or "'''" in stripped):
                in_docstring = not in_docstring
                if not in_docstring and docstring_content:
                    elements.append(f"MODULE: {' '.join(docstring_content)[:200]}")
                    break
                continue

            if in_docstring:
                docstring_content.append(stripped.strip('"').strip("'"))
                continue

            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].replace("class ", "").strip(":")
                elements.append(f"CLASS {class_name}")

            elif stripped.startswith("def ") or stripped.startswith("async def "):
                func_name = stripped.split("(")[0].replace("def ", "").replace("async ", "").strip()
                if not func_name.startswith("_"):
                    elements.append(f"FUNCTION {func_name}")

        return "\n".join(elements) if elements else None

    except Exception:
        return None


# ============================================================================
# BATCH LLM INTERACTION
# ============================================================================

def create_batch_prompt(file_infos: List[FileInfo], theme: str) -> str:
    """Create a single prompt for multiple files"""
    files_section = []

    for info in file_infos:
        files_section.append(f"""
---FILE: {info.path}---
{info.content}
""")

    combined = "\n".join(files_section)
    theme_instruction = f"\nContext: {theme}" if theme else ""

    return f"""Analyze these {len(file_infos)} Python files and provide brief documentation for each.{theme_instruction}

{combined}

Format your response EXACTLY like this for each file:
FILE: path/to/file.py
DOCS: Your concise explanation here (max 150 words)

FILE: path/to/another.py
DOCS: Your concise explanation here (max 150 words)
"""


def generate_batch_documentation(batch: List[FileInfo], model: str, theme: str) -> List[Dict[str, str]]:
    """Generate documentation for a batch of files"""
    if not batch:
        return []

    prompt = create_batch_prompt(batch, theme)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0.3,
                "num_predict": 250 * len(batch),
            },
            stream=False
        )

        response_text = response["message"]["content"]

        # ---------- FLEXIBLE PARSER (Option 2) ----------
        results = []
        current_file = None
        current_docs = []

        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Match: FILE: path OR markdown headers ## path / ### path
            if line.startswith("FILE:") or line.startswith("##"):
                # Save previous file
                if current_file and current_docs:
                    results.append({
                        "path": current_file,
                        "documentation": "\n".join(current_docs).strip()
                    })

                current_file = (
                    line.replace("FILE:", "")
                        .lstrip("#")
                        .strip()
                )
                current_docs = []

            else:
                if current_file:
                    current_docs.append(line)

        # Save last file
        if current_file and current_docs:
            results.append({
                "path": current_file,
                "documentation": "\n".join(current_docs).strip()
            })

        # Fallback only if nothing parsed
        if not results:
            print("⚠️ Batch parsing failed, using fallback")
            results = [
                {"path": f.path, "documentation": "📝 Documentation generated"}
                for f in batch
            ]

        return results
        # ------------------------------------------------

    except Exception as e:
        print(f"❌ Batch generation error: {e}")
        return [
            {"path": f.path, "documentation": f"❌ Error: {str(e)[:100]}"}
            for f in batch
        ]



# ============================================================================
# OPTIMIZED BATCH PROCESSING
# ============================================================================

def process_repository(repo_path: Path, model: str, max_workers: int, theme: str, job_id: str, subdir: Optional[str] = None) -> List[Dict[str, str]]:
    """Process files with subdirectory support"""

    # Determine search path
    if subdir:
        search_path = repo_path / subdir
        print(f"🔍 Searching only in subdirectory: {search_path}")
    else:
        search_path = repo_path
        print(f"🔍 Searching entire repository: {search_path}")
    
    if not search_path.exists():
        raise Exception(f"Path does not exist: {search_path}")

    # Stage 1: File discovery
    job_store[job_id]["status"] = f"Discovering files in {subdir or 'root'}"
    all_py_files = list(search_path.rglob("*.py"))
    print(f"📂 Found {len(all_py_files)} .py files in {search_path}")

    # Filter files
    py_files = [f for f in all_py_files if not should_skip(f)]

    if not py_files:
        print(f"⚠️ No valid files after filtering from {len(all_py_files)} total")
        return []

    print(f"✅ Processing {len(py_files)} files after filtering:")
    for f in py_files[:10]:  # Show first 10
        print(f"   - {f.relative_to(repo_path)}")
    if len(py_files) > 10:
        print(f"   ... and {len(py_files) - 10} more")

    # Stage 2: Parallel analysis
    job_store[job_id]["status"] = "Analyzing code"
    file_infos: List[FileInfo] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(analyze_file, f): f for f in py_files}

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                content = future.result()
                if content:
                    info = FileInfo(
                        path=str(file_path.relative_to(repo_path)),
                        content=content,
                        size=len(content)
                    )
                    info.importance_score = calculate_importance(file_path, content)
                    file_infos.append(info)
            except Exception as e:
                print(f"⚠️ Failed to analyze {file_path}: {e}")
                continue

    if not file_infos:
        return []

    print(f"📊 Analyzed {len(file_infos)} files successfully")

    # Sort by importance
    file_infos.sort(key=lambda x: (-x.importance_score, x.size))

    # Stage 3: Create batches
    job_store[job_id]["status"] = "Creating batches"
    batches = []
    current_batch = []
    current_batch_size = 0

    for info in file_infos:
        estimated_tokens = len(info.content) // 4

        if (current_batch_size + estimated_tokens > MAX_BATCH_TOKENS or
                len(current_batch) >= BATCH_SIZE):
            if current_batch:
                batches.append(current_batch)
            current_batch = [info]
            current_batch_size = estimated_tokens
        else:
            current_batch.append(info)
            current_batch_size += estimated_tokens

    if current_batch:
        batches.append(current_batch)

    print(f"📦 Created {len(batches)} batches")

    # Update job store
    job_store[job_id]["total_batches"] = len(batches)
    job_store[job_id]["completed_batches"] = 0

    # Stage 4: Process batches
    job_store[job_id]["status"] = "Generating documentation"
    all_results = []

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_BATCHES) as executor:
        future_to_batch = {
            executor.submit(generate_batch_documentation, batch, model, theme): idx
            for idx, batch in enumerate(batches)
        }

        for future in as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            try:
                results = future.result()
                all_results.extend(results)

                # Update progress
                job_store[job_id]["completed_batches"] += 1
                completed = job_store[job_id]["completed_batches"]
                total = job_store[job_id]["total_batches"]
                progress = 30 + int((completed / total) * 40)
                job_store[job_id]["progress"] = progress

                print(f"✅ Batch {completed}/{total} complete ({progress}%)")

            except Exception as e:
                print(f"❌ Batch {batch_idx} error: {e}")
                continue

    return all_results


# ============================================================================
# WORKER FUNCTION
# ============================================================================

def worker_generate_docs(job_id: str, req: GenerateRequest):
    db = SessionLocal()
    tmp_dir = tempfile.mkdtemp(prefix="repo-")

    try:
        job_store[job_id]["status"] = "Parsing URL"
        job_store[job_id]["progress"] = 5
        
        # Parse URL to get base repo and subdirectory
        base_url, subdir = parse_github_url(req.repo_url)
        print(f"🔍 Base URL: {base_url}")
        print(f"🔍 Subdirectory: {subdir or 'None (root)'}")

        job_store[job_id]["status"] = "Cloning repository"
        job_store[job_id]["progress"] = 10

        if not branch_exists(base_url, req.branch, req.access_token):
            raise Exception(f"Branch '{req.branch}' does not exist")

        repo, subdir_path = clone_repository(req.repo_url, req.branch, req.access_token, tmp_dir)
        repo.git.clear_cache()
        repo.close()
        del repo
        repo_path = Path(tmp_dir)

        commit_hash = get_commit_hash(repo_path)

        # Check cache (include subdir in cache key)
        cache_key = f"{base_url}/{subdir}" if subdir else base_url
        

        if req.use_cache:
            print("use_cache =", req.use_cache)
            cached = get_cached_doc(db, cache_key, req.branch, commit_hash)
            if cached:
                job_store[job_id].update({
            "status": "Completed",
            "cached": True,
            "progress": 100,
            "output_file": cached.doc_path
            })
                print(f"✅ Using cached documentation from {cached.doc_path}")
                return
        else:
            print(f"🔄 Cache bypassed - generating fresh documentation")

        # Process files
        job_store[job_id]["status"] = "Processing files"
        job_store[job_id]["progress"] = 30

        results = process_repository(repo_path, req.model, req.max_workers, req.theme, job_id, subdir_path)

        if not results:
            search_path = repo_path / subdir_path if subdir_path else repo_path
            all_files = list(search_path.rglob("*.py"))
            error_msg = f"No documentable files in {subdir_path or 'repository'}. "
            if len(all_files) == 0:
                error_msg += "No .py files found."
            else:
                error_msg += f"Found {len(all_files)} .py files but all were filtered."

            job_store[job_id]["error"] = error_msg
            job_store[job_id]["status"] = "Failed"
            return

        # Build markdown
        job_store[job_id]["status"] = "Building document"
        job_store[job_id]["progress"] = 75

        docs = [f"# Repository Documentation\n"]
        if subdir_path:
            docs.append(f"**Subdirectory:** `{subdir_path}`\n")
        
        for item in results:
            docs.append(f"## `{item['path']}`\n\n{item['documentation']}\n")

        final_doc = "\n".join(docs)

        # Export
        job_store[job_id]["status"] = "Exporting"
        job_store[job_id]["progress"] = 90

        output_file = export_document(final_doc, req.format,req.template)

        folder = STORAGE_ROOT / sanitize_filename(cache_key) / commit_hash
        folder.mkdir(parents=True, exist_ok=True)

        final_path = folder / f"documentation.{req.format}"
        shutil.move(output_file, final_path)

        # Save to cache only if cache is enabled
        if req.use_cache:
            save_cached_doc(
                db,
                repo_url=cache_key,
                branch=req.branch,
                commit_hash=commit_hash,
                doc_path=str(final_path),
            )
            print(f"💾 Documentation cached at {final_path}")
        else:
            print(f"💾 Documentation saved (not cached) at {final_path}")

        job_store[job_id].update({
    "status": "Completed",
    "cached": False,
    "progress": 100,
    "output_file": str(final_path)
    })


    except Exception as e:
        job_store[job_id]["error"] = str(e)
        job_store[job_id]["status"] = "Failed"
        print(f"❌ Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            time.sleep(0.5)
            safe_rmtree(tmp_dir)
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")
        finally:
            db.close()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/health")
def health():
    try:
        ollama.list()
        return {"status": "healthy", "ollama": "connected"}
    except Exception:
        return {"status": "degraded", "ollama": "disconnected"}


@router.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(404, "Invalid Job Id")
    return job_store[job_id]


@router.get("/download/{job_id}")
def download(job_id: str):
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Invalid job_id")

    if job.get("error"):
        raise HTTPException(status_code=500, detail=job["error"])

    if job["status"] != "Completed" and not job["status"].startswith("Completed"):
        raise HTTPException(
            status_code=425,
            detail=f"Not ready. Status: {job['status']}, Progress: {job['progress']}%"
        )

    output_file = job.get("output_file")

    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="File not found")

    file_format = output_file.split('.')[-1]
    media_type_map = {
        "md": "text/markdown",
        "pdf": "application/pdf",
        "html": "text/html",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    media_type = media_type_map.get(file_format, "application/octet-stream")
    filename = f"documentation.{file_format}"

    return FileResponse(
        path=output_file,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )


@router.post("/list-branches")
def list_branches(req: BranchRequest):
    try:
        # Parse URL to get base repo
        base_url, _ = parse_github_url(req.repo_url)
        branches = list_remote_branches(base_url, req.access_token)
        if not branches:
            raise HTTPException(400, "No branches found")

        return {
            "default": "main" if "main" in branches else branches[0],
            "branches": branches
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/")
def root():
    return {
        "service": "Optimized Documentation Generator",
        "version": "2.1",
        "features": ["Subdirectory support", "Batch processing"],
        "endpoints": {
            "start": "/start-generation",
            "status": "/status/{job_id}",
            "download": "/download/{job_id}",
            "health": "/health"
        }
    }