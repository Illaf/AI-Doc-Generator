import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = """
You are a senior software engineer and technical writer.

Rules:
- Generate documentation ONLY from the given code
- Do NOT hallucinate APIs
- Be concise and accurate
- Output valid JSON only
"""

def analyze_code(code: str, language: str, filename: str) -> dict:
    prompt = f"""
Language: {language}
File: {filename}

Source Code:
{code}

Extract:
1. File overview
2. Classes (name, description, methods)
3. Functions (name, parameters, return value)
4. Important logic notes
5. Example usage (only if obvious)

Return JSON in this format:
{{
  "file": "{filename}",
  "language": "{language}",
  "overview": "",
  "classes": [],
  "functions": [],
  "notes": [],
  "examples": []
}}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        },
        timeout=120
    )

    response.raise_for_status()

    content = response.json()["message"]["content"]

    # IMPORTANT: Ollama sometimes adds text before/after JSON
    return content
