"""Load vector embeddings into pgvector."""

import numpy as np
from sentence_transformers import SentenceTransformer

from src.db.postgres_client import db
from src.utils.data_parser import DataParser


class VectorLoader:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.parser = DataParser()

    def create_vector_extension(self):
        """Enable pgvector extension and create embeddings table."""
        with db.get_cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_embeddings (
                    product_id VARCHAR(10) PRIMARY KEY,
                    description_embedding vector(384)  -- 384 dimensions for MiniLM
                );
            """)

    def generate_embeddings(self):
        """Generate embeddings for all product descriptions."""
        products = self.parser.parse_products()

        for _, product in products.iterrows():
            # Combine relevant text fields
            text = f"{product['NAME']} {product['DESCRIPTION']} {' '.join(product['TAGS'])}"

            # Generate embedding
            embedding = self.model.encode(text)

            # Store in database
            self._store_embedding(product["ID"], embedding)

    def _store_embedding(self, product_id: str, embedding: np.ndarray):
        """Store embedding in pgvector."""
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO product_embeddings (product_id, description_embedding)
                VALUES (%s, %s)
                ON CONFLICT (product_id) DO UPDATE
                SET description_embedding = EXCLUDED.description_embedding;
                """,
                (product_id, embedding.tolist()),
            )

    def load_all(self):
        """Create extension/table and generate/store all embeddings."""
        self.create_vector_extension()
        self.generate_embeddings()
        print("Vector embeddings loaded!")


if __name__ == "__main__":
    loader = VectorLoader()
    loader.load_all()
