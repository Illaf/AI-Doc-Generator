import pypandoc
import asyncio
import tempfile
import requests
from fastapi.responses import FileResponse
API_URL = "http://localhost:8000/generate-docs"
from services.templates import apply_template
from fastapi import HTTPException, Response

def export_document(markdown_content: str, output_format: str, template: str):
    """
    Convert markdown into a file and return the file PATH.
    Background tasks cannot return Response objects.
    
    Args:
        markdown_content: The markdown string
        output_format: "md", "html", "pdf", or "docx"
        template: UI template name (only applies to HTML/PDF)
    
    Returns:
        Path to the generated file
    """

    # Case 1: Plain markdown -> write to temp file (no template needed)
    if output_format == "md":
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
        tmp_file.write(markdown_content.encode("utf-8"))
        tmp_file.close()
        return tmp_file.name

    # Case 2: HTML with template
    if output_format == "html":
        print("template:",template)
        html_content = apply_template(markdown_content, template)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
        tmp_file.write(html_content)
        tmp_file.close()
        return tmp_file.name

    # Case 3: PDF with template
    # Strategy: Generate HTML with template first, then convert HTML -> PDF
    if output_format == "pdf":
        # Step 1: Create templated HTML
        html_content = apply_template(markdown_content, template)
        
        # Step 2: Save HTML to temp file
        tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
        tmp_html.write(html_content)
        tmp_html.close()
        
        # Step 3: Convert HTML -> PDF using pypandoc
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        
        try:
            pypandoc.convert_file(
                tmp_html.name,
                to="pdf",
                format="html",
                outputfile=output_file,
                extra_args=[
                    "--pdf-engine=weasyprint",  # or wkhtmltopdf if you have it
                    "--standalone"
                ]
            )
        except Exception as e:
            # Fallback: if pypandoc PDF fails, try without template
            try:
                pypandoc.convert_text(
                    markdown_content,
                    to="pdf",
                    format="md",
                    outputfile=output_file,
                    extra_args=["--standalone"]
                )
            except Exception as fallback_error:
                raise HTTPException(500, f"PDF conversion failed: {str(e)}")
        
        # Clean up temp HTML
        import os
        try:
            os.unlink(tmp_html.name)
        except:
            pass
        
        return output_file

    # Case 4: DOCX (no template, use pypandoc directly)
    if output_format == "docx":
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
        
        try:
            pypandoc.convert_text(
                markdown_content,
                to="docx",
                format="md",
                outputfile=output_file,
                extra_args=["--standalone"]
            )
        except Exception as e:
            raise HTTPException(500, f"DOCX conversion failed: {str(e)}")
        
        return output_file

    # Unknown format
    raise HTTPException(400, f"Unsupported output format: {output_format}")