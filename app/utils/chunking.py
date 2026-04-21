from __future__ import annotations


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if not text:
        return []

    overlap = max(0, min(chunk_overlap, chunk_size - 1))
    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])

        if end >= text_length:
            break

        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks
