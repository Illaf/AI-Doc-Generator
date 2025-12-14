def detect_language(filename: str) -> str:
    ext = filename.split(".")[-1].lower()

    return {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "cs": "csharp",
        "go": "go",
        "cpp": "cpp",
        "c": "c"
    }.get(ext, "unknown")
