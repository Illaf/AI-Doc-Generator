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

def call_llama(prompt: str, model: str = "llama3.2") -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
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

    return json.loads(content)
