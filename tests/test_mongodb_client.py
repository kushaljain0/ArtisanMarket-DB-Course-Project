from src.db.mongodb_client import mongo_client


def test_get_collection():
    col = mongo_client.get_collection("user_preferences")
    assert col is not None


def test_create_indexes():
    mongo_client.create_indexes()
    # If no exception, indexes are created
    assert True
