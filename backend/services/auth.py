from typing import Optional
from datetime import datetime, timedelta
import os
import base64
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from passlib.context import CryptContext
from jose import jwt, JWTError
import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter
from dotenv import load_dotenv
auth_router = APIRouter()
load_dotenv()
# --------------------------
# Config & utils
# --------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev_jwt_secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URL", "http://localhost:8000/github/callback")
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if ENCRYPTION_KEY is None:
    # For dev only: generate a key — DO NOT use this in production
    ENCRYPTION_KEY = Fernet.generate_key().decode()

fernet = Fernet(ENCRYPTION_KEY.encode())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --------------------------
# Database
# --------------------------

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    github = relationship("GitHubAccount", uselist=False, back_populates="user")


class GitHubAccount(Base):
    __tablename__ = "github_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    github_user_id = Column(String, nullable=False)
    username = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    encrypted_access_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="github")


Base.metadata.create_all(bind=engine)


class SignupIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expire: Optional[timedelta] = None):
    to_encode = data.copy()
    if expire:
        time_update = datetime.utcnow() + expire
    else:
        time_update = datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    to_encode.update({"exp": time_update})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = None
    auth_header = request.headers.get("Authorization")
    print("🔎 Header Authorization:", auth_header)
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    if not token:
        token = request.query_params.get("token")
        print("🔎 Query Token:", token)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials - no token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception
    
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


@auth_router.post("/auth/signup", response_model=TokenOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Given mail already exists")
    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token}


@auth_router.post("/auth/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm has username and password fields; we'll treat username as email
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token}


@auth_router.get("/github/connect")
def github_connect(current_user: User = Depends(get_current_user)):
    """
    Initiates GitHub OAuth flow. Creates a state token containing user_id
    to preserve authentication across the redirect.
    """
    print("DEBUG -> Entered /github/connect")
    print("DEBUG Current User ID:", current_user.id)

    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub client id not configured")
    if not GITHUB_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="GitHub redirect uri not configured")

    # Create state token containing user_id with short expiration (10 minutes)
    state_token = create_access_token(
        {"user_id": current_user.id, "purpose": "github_oauth"},
        expire=timedelta(minutes=10)
    )

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "repo read:user",
        "state": state_token,  # Pass state to preserve user session
        "allow_signup": "false"
    }

    # Properly encoded query string
    query = "&".join([f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items()])
    url = "https://github.com/login/oauth/authorize"

    print("DEBUG FULL URL:", url + "?" + query)
    return RedirectResponse(url + "?" + query)


@auth_router.get("/github/callback")
async def github_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    GitHub OAuth callback. Uses state token to identify user instead of
    requiring authentication, since this endpoint is hit by redirect.
    """
    if code is None:
        raise HTTPException(status_code=400, detail="No code provided by GitHub")
    
    if state is None:
        raise HTTPException(status_code=400, detail="No state token provided")

    # Decode state token to get user_id
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        purpose = payload.get("purpose")
        
        if purpose != "github_oauth":
            raise HTTPException(status_code=400, detail="Invalid state token")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid state token")
        
        user_id = int(user_id)
    except JWTError as e:
        print(f"State token decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid or expired state token")

    # Get user from database
    current_user = get_user_by_id(db, user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    async with httpx.AsyncClient() as client:
        headers = {"Accept": "application/json"}
        data = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
        }
        resp = await client.post(token_url, headers=headers, data=data)
        resp.raise_for_status()
        token_json = resp.json()

    access_token = token_json.get("access_token")
    if not access_token:
        error = token_json.get("error", "unknown")
        error_desc = token_json.get("error_description", "Failed to obtain access token")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error} - {error_desc}")

    # Fetch GitHub user info
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json"
        }
        user_resp = await client.get("https://api.github.com/user", headers=headers)
        user_resp.raise_for_status()
        gh_user = user_resp.json()

    # Store or update GitHub account
    encrypted = encrypt_token(access_token)
    gh_account = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if gh_account:
        gh_account.github_user_id = str(gh_user.get("id"))
        gh_account.username = gh_user.get("login")
        gh_account.avatar_url = gh_user.get("avatar_url")
        gh_account.encrypted_access_token = encrypted
    else:
        gh_account = GitHubAccount(
            user_id=current_user.id,
            github_user_id=str(gh_user.get("id")),
            username=gh_user.get("login"),
            avatar_url=gh_user.get("avatar_url"),
            encrypted_access_token=encrypted,
        )
        db.add(gh_account)
    
    db.commit()
    
    # return {
    #     "detail": "GitHub account linked successfully",
    #     "username": gh_user.get("login"),
    #     "avatar_url": gh_user.get("avatar_url")
    # }
    return RedirectResponse(
    url="http://localhost:3000/dashboard?github=linked",
    status_code=302
    )


@auth_router.get("/github/repos")
async def get_github_repos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gh = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id
    ).first()
    if not gh:
        raise HTTPException(status_code=400, detail="GitHub account not linked")
    
    token = decrypt_token(gh.encrypted_access_token)
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        resp = await client.get("https://api.github.com/user/repos?per_page=100", headers=headers)
        resp.raise_for_status()
        repos = resp.json()
    
    out = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "private": r.get("private"),
            "html_url": r.get("html_url")
        }
        for r in repos
    ]
    return {"repos": out}


@auth_router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }