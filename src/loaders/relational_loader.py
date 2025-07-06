"""Load data into PostgreSQL database."""

from src.db.postgres_client import db
from src.utils.data_parser import DataParser


class RelationalLoader:
    def __init__(self):
        self.db = db
        self.parser = DataParser()

    def load_categories(self):
        """Load categories into PostgreSQL."""
        categories = self.parser.parse_categories()

        with self.db.get_cursor() as cursor:
            for _, row in categories.iterrows():
                query = """
                        INSERT INTO categories (id, name, description)
                        VALUES (%(ID)s, %(NAME)s, %(DESCRIPTION)s) ON CONFLICT (id) DO NOTHING;
                        """
                cursor.execute(query, row.to_dict())

        print(f"Loaded {len(categories)} categories")

    def load_sellers(self):
        """Load sellers into PostgreSQL."""
        sellers = self.parser.parse_sellers()
        with self.db.get_cursor() as cursor:
            for _, row in sellers.iterrows():
                query = """
                    INSERT INTO sellers (id, name, specialty, rating, joined)
                    VALUES (%(ID)s, %(NAME)s, %(SPECIALTY)s, %(RATING)s, %(JOINED)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                cursor.execute(query, row.to_dict())
        print(f"Loaded {len(sellers)} sellers")

    def load_users(self):
        """Load users into PostgreSQL."""
        users = self.parser.parse_users()
        with self.db.get_cursor() as cursor:
            for _, row in users.iterrows():
                query = """
                    INSERT INTO users (id, name, email, join_date, location, interests)
                    VALUES (%(ID)s, %(NAME)s, %(EMAIL)s, %(JOIN_DATE)s, %(LOCATION)s, %(INTERESTS)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                # Convert interests list to comma-separated string
                row_dict = row.to_dict()
                row_dict["INTERESTS"] = ",".join(row_dict["INTERESTS"])
                cursor.execute(query, row_dict)
        print(f"Loaded {len(users)} users")

    def load_products(self):
        """Load products into PostgreSQL."""
        products = self.parser.parse_products()
        categories = self.parser.parse_categories()

        # Create a mapping from category name to category id
        category_map = dict(zip(categories["NAME"], categories["ID"], strict=False))

        with self.db.get_cursor() as cursor:
            for _, row in products.iterrows():
                # Map category name to category id
                category_name = row["CATEGORY"]
                category_id = category_map.get(category_name)

                if category_id is None:
                    print(
                        f"Warning: Category '{category_name}' not found for product {row['ID']}"
                    )
                    continue

                query = """
                    INSERT INTO products (id, name, category_id, price, seller_id, description, tags, stock)
                    VALUES (%(ID)s, %(NAME)s, %(category_id)s, %(PRICE)s, %(SELLER_ID)s, %(DESCRIPTION)s, %(tags)s, %(STOCK)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                # Convert tags list to comma-separated string
                row_dict = row.to_dict()
                row_dict["tags"] = ",".join(row_dict["TAGS"])
                row_dict["category_id"] = category_id
                cursor.execute(query, row_dict)
        print(f"Loaded {len(products)} products")

    def load_all(self):
        """Load all data into PostgreSQL."""
        print("Creating tables...")
        self.db.create_tables()

        print("Loading categories...")
        self.load_categories()
        print("Loading sellers...")
        self.load_sellers()
        print("Loading users...")
        self.load_users()
        print("Loading products...")
        self.load_products()
        print("Relational data loading complete!")


if __name__ == "__main__":
    loader = RelationalLoader()
    loader.load_all()
