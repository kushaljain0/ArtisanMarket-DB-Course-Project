"""Generate random purchase history and load into databases."""

import random
from datetime import datetime, timedelta

import pandas as pd

from src.db.postgres_client import db
from src.db.neo4j_client import neo4j_client
from src.utils.data_parser import DataParser


class PurchaseGenerator:
    def __init__(self):
        self.parser = DataParser()
        self.users = self.parser.parse_users()
        self.products = self.parser.parse_products()

    def generate_purchases(self, num_purchases: int = 100) -> pd.DataFrame:
        """Generate random purchases based on user interests."""
        purchases = []
        users = self.users
        products = self.products

        for _ in range(num_purchases):
            user = users.sample(1).iloc[0]
            # Filter products by user interests (tags)
            user_interests = user["INTERESTS"]
            matching_products = products[
                products["TAGS"].apply(
                    lambda tags, interests=user_interests: any(
                        interest in tags for interest in interests
                    )
                )
            ]
            product = (
                products.sample(1).iloc[0]
                if matching_products.empty
                else matching_products.sample(1).iloc[0]
            )
            # Respect user join date (purchase after join)
            join_date = user["JOIN_DATE"]
            purchase_date = join_date + timedelta(days=random.randint(0, 180))
            if purchase_date > datetime.now():
                purchase_date = datetime.now()
            quantity = random.randint(1, 3)
            purchases.append(
                {
                    "user_id": user["ID"],
                    "product_id": product["ID"],
                    "quantity": quantity,
                    "purchase_date": purchase_date.strftime("%Y-%m-%d"),
                    "unit_price": product["PRICE"],
                    "total_price": product["PRICE"] * quantity,
                }
            )
        return pd.DataFrame(purchases)

    def save_purchases(self, purchases: pd.DataFrame, filename: str = "purchases.csv"):
        """Save generated purchases to CSV."""
        purchases.to_csv(filename, index=False)

    def load_purchases_to_postgres(self, purchases: pd.DataFrame):
        """Load purchases into PostgreSQL orders and order_items tables."""
        # Group purchases by user and date to create orders
        orders = []
        order_items = []
        order_id = 1

        # Group purchases by user and date (same day purchases = same order)
        purchase_groups = purchases.groupby(["user_id", "purchase_date"])

        for (user_id, purchase_date), group in purchase_groups:
            total_amount = float(group["total_price"].sum())  # Convert to native Python float

            # Create order
            orders.append(
                {
                    "id": order_id,
                    "user_id": user_id,
                    "order_date": purchase_date,
                    "total_amount": total_amount,
                    "status": "completed",
                }
            )

            # Create order items
            for _, purchase in group.iterrows():
                order_items.append(
                    {
                        "order_id": order_id,
                        "product_id": purchase["product_id"],
                        "quantity": int(purchase["quantity"]),  # Convert to native Python int
                        "unit_price": float(purchase["unit_price"]),  # Convert to native Python float
                        "total_price": float(purchase["total_price"]),  # Convert to native Python float
                    }
                )

            order_id += 1

        # Insert orders
        with db.get_cursor() as cursor:
            for order in orders:
                cursor.execute(
                    """
                    INSERT INTO orders (id, user_id, order_date, total_amount, status)
                    VALUES (%(id)s, %(user_id)s, %(order_date)s, %(total_amount)s, %(status)s)
                    ON CONFLICT (id) DO NOTHING;
                """,
                    order,
                )

            # Insert order items
            for item in order_items:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                    VALUES (%(order_id)s, %(product_id)s, %(quantity)s, %(unit_price)s, %(total_price)s)
                """,
                    item,
                )

        print(
            f"Loaded {len(orders)} orders and {len(order_items)} order items to PostgreSQL"
        )

    def load_purchases_to_neo4j(self, purchases: pd.DataFrame):
        """Load purchases into Neo4j as PURCHASED relationships."""
        for _, purchase in purchases.iterrows():
            neo4j_client.add_purchase(
                user_id=purchase["user_id"],
                product_id=purchase["product_id"],
                quantity=purchase["quantity"],
                date=purchase["purchase_date"],
            )

        print(f"Loaded {len(purchases)} purchase relationships to Neo4j")

    def generate_and_load_all(self, num_purchases: int = 100):
        """Generate purchases and load into all databases."""
        print(f"Generating {num_purchases} purchases...")
        purchases = self.generate_purchases(num_purchases)

        print("Saving purchases to CSV...")
        self.save_purchases(purchases)

        print("Loading purchases to PostgreSQL...")
        self.load_purchases_to_postgres(purchases)

        print("Loading purchases to Neo4j...")
        self.load_purchases_to_neo4j(purchases)

        print(f"Successfully generated and loaded {len(purchases)} purchases")


if __name__ == "__main__":
    generator = PurchaseGenerator()
    generator.generate_and_load_all()
