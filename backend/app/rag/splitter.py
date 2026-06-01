from dataclasses import dataclass


@dataclass(frozen=True)
class TextSplitter:
    chunk_size: int = 120
    chunk_overlap: int = 0

    def split_text(self, text: str) -> list[str]:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return self._split_by_length(text.strip())

        chunks: list[str] = []
        current = ""
        for line in lines:
            if len(line) > self.chunk_size:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_by_length(line))
                continue

            candidate = line if not current else f"{current}\n{line}"
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                chunks.append(current)
                current = line

        if current:
            chunks.append(current)

        return chunks

    def _split_by_length(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        step = self.chunk_size - self.chunk_overlap
        for index in range(0, len(text), step):
            chunk = text[index : index + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks
