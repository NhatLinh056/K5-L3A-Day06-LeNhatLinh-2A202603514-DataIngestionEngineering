"""Exact cosine search with persistent pgvector storage."""
import math
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive")
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            connection.execute(f"""CREATE TABLE IF NOT EXISTS day6_chunks (
                strategy TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                source TEXT NOT NULL,
                page INTEGER NOT NULL,
                text TEXT NOT NULL,
                metadata JSONB NOT NULL,
                embedding VECTOR({self.dimensions}) NOT NULL,
                PRIMARY KEY (strategy, chunk_id)
            )""")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and vector counts differ")
        for vector in vectors:
            if len(vector) != self.dimensions or not all(math.isfinite(value) for value in vector):
                raise ValueError("Invalid embedding dimensions or values")
        rows = [(strategy, chunk.chunk_id, chunk.document_id, chunk.source,
                 chunk.page, chunk.text, Jsonb(chunk.metadata),
                 "[" + ",".join(str(value) for value in vector) + "]")
                for chunk, vector in zip(chunks, vectors)]
        with psycopg.connect(self.database_url) as connection:
            # Replace one strategy atomically so changed source removes stale chunks.
            connection.execute("DELETE FROM day6_chunks WHERE strategy = %s", (strategy,))
            with connection.cursor() as cursor:
                cursor.executemany("""INSERT INTO day6_chunks
                    (strategy, chunk_id, document_id, source, page, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)""", rows)

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if len(query_vector) != self.dimensions or not all(math.isfinite(x) for x in query_vector):
            raise ValueError("Invalid query vector")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if filters and (set(filters) != {"chapter"} or not isinstance(filters["chapter"], int)):
            raise ValueError("Only an integer chapter filter is supported")
        vector = "[" + ",".join(str(value) for value in query_vector) + "]"
        where = "strategy = %s"
        parameters: list[Any] = [vector, strategy]
        if filters:
            where += " AND page = %s"
            parameters.append(filters["chapter"])
        parameters.extend([vector, top_k])
        with psycopg.connect(self.database_url) as connection:
            rows = connection.execute(f"""SELECT chunk_id, document_id, source, page,
                text, metadata, 1 - (embedding <=> %s::vector) AS score
                FROM day6_chunks WHERE {where}
                ORDER BY embedding <=> %s::vector LIMIT %s""", parameters).fetchall()
        return [{"chunk_id": row[0], "document_id": row[1], "source": row[2],
                 "page": row[3], "text": row[4], "metadata": row[5],
                 "score": float(row[6])} for row in rows]
