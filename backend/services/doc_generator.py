from services.language import detect_language
from services.llm_client import analyze_code
from utils.chunker import chunk_code

async def generate_docs_for_file(filename: str, code: str):
    language = detect_language(filename)
    chunks = chunk_code(code)

    results = []

    for chunk in chunks:
        doc = await analyze_code(chunk, language, filename)
        results.append(doc)

    return merge_chunks(results)


def merge_chunks(chunk_docs: list) -> dict:
    base = chunk_docs[0]

    for doc in chunk_docs[1:]:
        base["classes"].extend(doc.get("classes", []))
        base["functions"].extend(doc.get("functions", []))
        base["notes"].extend(doc.get("notes", []))
        base["examples"].extend(doc.get("examples", []))

    return base
