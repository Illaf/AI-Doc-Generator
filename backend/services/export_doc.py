import pypandoc
import asyncio
import tempfile
import requests
from fastapi.responses import FileResponse
API_URL = "http://localhost:8000/generate-docs"

from fastapi import HTTPException, Response

def export_document(markdown_content: str, output_format: str):
    """
    Convert markdown into a file and return the file PATH.
    Background tasks cannot return Response objects.
    """

    # Case 1: plain markdown -> write to temp file
    if output_format == "md":
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
        tmp_file.write(markdown_content.encode("utf-8"))
        tmp_file.close()
        return tmp_file.name

    # Case 2: DOCX or PDF
    suffix = f".{output_format}"
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name

    try:
        pypandoc.convert_text(
            markdown_content,
            to=output_format,
            format="md",
            outputfile=output_file,
            extra_args=["--standalone"]
        )
    except Exception as e:
        raise HTTPException(500, f"Document conversion failed: {str(e)}")

    return output_file  # <== ✔ return file path only
