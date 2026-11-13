"""Local semantic embeddings shared by every strategy."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Sentence Transformers model; errors are reported, never mocked."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_embedding_dimension()
        if not self.dimensions:
            raise ValueError("Embedding model did not report dimensions")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, batch_size=32, show_progress_bar=True).tolist()

    def embed_query(self, question: str) -> list[float]:
        return self.model.encode(question).tolist()
