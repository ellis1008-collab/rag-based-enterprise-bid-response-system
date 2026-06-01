from app.rag import TextSplitter


def split_text_by_length(content: str, chunk_size: int) -> list[str]:
    return TextSplitter(chunk_size=chunk_size).split_text(content)
