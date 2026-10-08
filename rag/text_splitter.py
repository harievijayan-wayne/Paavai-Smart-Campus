from typing import List, Dict, Any
from app.core.config import settings


class TextSplitter:
    """
    Splits long documents into semantically coherent chunks with overlap.
    """

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split a list of extracted pages into chunks while preserving page numbers.
        Input: [{"page": 1, "text": "..."}]
        Output: [{"chunk_index": 0, "content": "...", "page": 1, "token_count": 85}]
        """
        chunks = []
        chunk_idx = 0

        for page_data in pages:
            page_num = page_data.get("page", 1)
            text = page_data.get("text", "").strip()
            if not text:
                continue

            page_chunks = self.split_text(text)
            for c_text in page_chunks:
                # Approximation of tokens by word count
                tokens = len(c_text.split())
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": c_text,
                    "page": page_num,
                    "token_count": tokens,
                })
                chunk_idx += 1

        return chunks

    def split_text(self, text: str) -> List[str]:
        """Split raw text by paragraphs/sentences with overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Retain overlap from end of previous chunk
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                else:
                    # Single paragraph exceeds chunk_size, split by sentences
                    sentences = para.replace(". ", ".\n").split("\n")
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                            current_chunk = f"{current_chunk} {sentence}".strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


text_splitter = TextSplitter()
