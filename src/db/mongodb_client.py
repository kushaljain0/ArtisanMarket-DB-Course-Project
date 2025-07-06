"""MongoDB connection and utilities."""

from pymongo import MongoClient
from pymongo.database import Database

from src.config import MONGO_CONFIG


class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(MONGO_CONFIG["uri"])
        self.db: Database = self.client[MONGO_CONFIG["database"]]

    def get_collection(self, name: str):
        """Get a MongoDB collection."""
        return self.db[name]

    def create_indexes(self):
        """Create necessary indexes."""
        # Reviews: index on product_id, user_id
        self.db["reviews"].create_index("product_id")
        self.db["reviews"].create_index("user_id")
        # Product specs: index on product_id
        self.db["product_specs"].create_index("product_id")
        # Seller profiles: index on seller_id
        self.db["seller_profiles"].create_index("seller_id")
        # User preferences: index on user_id
        self.db["user_preferences"].create_index("user_id")


# Singleton instance
mongo_client = MongoDBClient()
