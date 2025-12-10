THEMES = {
    "default": {
        "description": "Clean, neutral formatting.",
        "tone": "neutral",
        "detail": "medium",
        "heading_style": "# {title}",
        "extra_markdown": ""
    },
    "technical": {
        "description": "Engineering-grade documentation.",
        "tone": "technical",
        "detail": "high",
        "heading_style": "# 🔧 {title}",
        "extra_markdown": "\n> **Technical Documentation Generated Automatically**\n"
    },
    "executive": {
        "description": "Business summaries and insights.",
        "tone": "formal",
        "detail": "low",
        "heading_style": "# 📌 {title}",
        "extra_markdown": "\n> **Executive Summary — Value-focused, not code-focused.**\n"
    },
    "research": {
        "description": "Thesis/report style output.",
        "tone": "academic",
        "detail": "very_high",
        "heading_style": "# 🧪 {title}",
        "extra_markdown": "---\n*Generated in academic tone.*\n---\n"
    }
}

def build_prompt(file_content:str,theme:str):
    cfg=THEMES.get(theme, THEMES["default"])
    return f"""
You are an AI assistant generating documentation.

Write documentation with the following instructions:

- Tone: **{cfg['tone']}**
- Depth of detail: **{cfg['detail']}**
- Audience: Adjust tone to match intended theme.
- Format: Use clear markdown headings, lists, tables, sections.

Rules:
- Avoid irrelevant content.
- Include purpose of the file, important classes, functions.
- Include examples if applicable.

Here is the code to document:
{file_content}
"""