from fastapi import APIRouter
from services.doc_generator import generate_docs_for_file
from utils.markdown import generate_markdown

doc_router = APIRouter()

@doc_router.post("/generate-doc")
async def generate_docs(files: dict):
    """
    files = {
        "auth.js": "code...",
        "main.py": "code..."
    }
    """

    docs = []

    for filename, code in files.items():
        doc = await generate_docs_for_file(filename, code)
        docs.append(doc)

    markdown = generate_markdown(docs)

    return {
        "docs": docs,
        "markdown": markdown
    }
