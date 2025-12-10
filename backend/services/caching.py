from pathlib import Path
import git,os,re
from sqlalchemy.orm import Session
# DB & storage imports (add near other imports)
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import hashlib
import urllib.parse

DB_PATH = os.environ.get("DOCGEN_DB", "sqlite:///./docgen.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_latest_commit_hash(repo_path:Path) -> str:
    repo= git.Repo(repo_path)
    return repo.head.commit.hexsha

class RepoCache(Base):
    __tablename__ = "repo_cache"
    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String, index=True, nullable=False)
    branch = Column(String, nullable=False, default="master")
    commit_hash = Column(String, index=True, nullable=False)
    doc_path = Column(String, nullable=False)  # file system path to markdown/pdf
    format = Column(String, nullable=False, default="md")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

STORAGE_ROOT = Path(os.environ.get("DOC_STORAGE", "./generated_docs"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sanitize_filename(value: str) -> str:
    """
    Convert URLs or strings into safe filenames by removing unsafe characters.
    """
    # Remove protocol
    value = re.sub(r'^https?://', '', value)
    
    # Replace any unsafe char with underscore
    value = re.sub(r'[^a-zA-Z0-9._-]', '_', value)
    
    # Trim repeated underscores
    value = re.sub(r'__+', '_', value)
    
    # Strip leading/trailing underscores
    value = value.strip("_")
    
    return value


def get_repo_name_from_url(url: str) -> str:
    """
    Make a safe short repo name from URL. e.g. https://github.com/user/repo.git -> user_repo
    """
    # strip .git and scheme
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/").rstrip(".git")
    # remove leading slash
    if path.startswith("/"):
        path = path[1:]
    return path.replace("/", "_")

def storage_dir(repo_url:str,commit_hash:str) -> Path:
    repo_name= get_repo_name_from_url(repo_url)
    return STORAGE_ROOT/repo_name/commit_hash

def get_commit_hash(repo_path: Path) -> str:
    repo = git.Repo(repo_path)
    return str(repo.head.commit.hexsha)


def save_final_doc_to_stoage(final_doc:str,repo_url:str,commit_hash:str,fmt:str = "md"):
    d=storage_dir(repo_url,commit_hash)
    d.mkdir(parents=True, exist_ok=True)

    if(fmt == "md"):
        outpath = d/"doc.md"
        outpath.write_text(final_doc,encoding="utf-8")

    else:
        outpath=d/f"doc.{fmt}"
        outpath.write_text(final_doc,encoding="utf-8")
    return str(outpath)

def get_cached_doc(db_session,repo_url:str,branch:str,commit_hash:str):
    return db_session.query(RepoCache).filter(RepoCache.repo_url== repo_url).filter(RepoCache.branch == branch).filter(RepoCache.commit_hash == commit_hash).first()

# ---------- DB helpers ----------
def get_cached_doc(db: Session, repo_url: str, branch: str, commit_hash: str):
    return (
        db.query(RepoCache)
        .filter(
            RepoCache.repo_url == repo_url,
            RepoCache.branch == branch,
            RepoCache.commit_hash == commit_hash
        )
        .first()
    )

def save_cached_doc(db: Session, repo_url, branch, commit_hash, doc_path):
    entry = RepoCache(
        repo_url=repo_url,
        branch=branch,
        commit_hash=commit_hash,
        doc_path=doc_path
    )
    db.add(entry)
    db.commit()


             
            



