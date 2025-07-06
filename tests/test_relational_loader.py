from src.db.postgres_client import db
from src.loaders.relational_loader import RelationalLoader


def test_load_categories():
    loader = RelationalLoader()
    loader.load_categories()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM categories;")
        assert cursor.fetchone()["cnt"] > 0


def test_load_sellers():
    loader = RelationalLoader()
    loader.load_sellers()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM sellers;")
        assert cursor.fetchone()["cnt"] > 0


def test_load_users():
    loader = RelationalLoader()
    loader.load_users()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM users;")
        assert cursor.fetchone()["cnt"] > 0


def test_load_products():
    loader = RelationalLoader()
    loader.load_products()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM products;")
        assert cursor.fetchone()["cnt"] > 0
