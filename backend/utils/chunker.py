def chunk_code(code: str, max_chars: int = 6000):
    lines = code.splitlines()
    chunks = []
    current_chunk = []

    current_size = 0

    for line in lines:
        current_chunk.append(line)
        current_size += len(line)

        if current_size >= max_chars:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks
