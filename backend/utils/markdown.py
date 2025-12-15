def generate_markdown(docs: list) -> str:
    md = "# 📘 Project Documentation\n\n"

    for doc in docs:
        md += f"## {doc['file']}\n\n"
        md += f"**Language:** {doc['language']}\n\n"
        md += f"{doc['overview']}\n\n"

        if doc["classes"]:
            md += "### Classes\n"
            for cls in doc["classes"]:
                md += f"#### {cls['name']}\n"
                md += f"{cls.get('description', '')}\n\n"

                for method in cls.get("methods", []):
                    md += f"- `{method['name']}({', '.join(method.get('params', []))})`\n"

        if doc["functions"]:
            md += "\n### Functions\n"
            for fn in doc["functions"]:
                md += f"- `{fn['name']}({', '.join(fn.get('params', []))}) → {fn.get('returns', '')}`\n"

        if doc["notes"]:
            md += "\n### Notes\n"
            for note in doc["notes"]:
                md += f"- {note}\n"

        md += "\n---\n\n"

    return md
