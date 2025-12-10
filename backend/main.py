from fastapi import FastAPI
from services.doc_gen import router
from services.auth import auth_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI(title="OptimizedDocGenerator", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)  # no prefix
app.include_router(auth_router)
