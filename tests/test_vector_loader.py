from src.db.postgres_client import db
from src.loaders.vector_loader import VectorLoader


def test_create_vector_extension():
    loader = VectorLoader()
    loader.create_vector_extension()
    # Check table exists
    with db.get_cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.product_embeddings') AS exists;")
        assert cursor.fetchone()["exists"] == "product_embeddings"


def test_generate_embeddings():
    loader = VectorLoader()
    loader.create_vector_extension()
    loader.generate_embeddings()
    # Check at least one embedding exists
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM product_embeddings;")
        assert cursor.fetchone()["cnt"] > 0
