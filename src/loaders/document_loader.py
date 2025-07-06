"""Load data into MongoDB collections."""

import random
from datetime import datetime, timedelta
from typing import List

from src.db.mongodb_client import mongo_client
from src.utils.data_parser import DataParser


class DocumentLoader:
    def __init__(self):
        self.db = mongo_client
        self.parser = DataParser()

    def load_reviews(self):
        """Load product reviews with nested comments."""
        products = self.parser.parse_products()
        users = self.parser.parse_users()
        reviews_collection = self.db.get_collection("reviews")

        # Generate realistic reviews for each product
        for _, product in products.iterrows():
            # Generate 1-5 reviews per product
            num_reviews = random.randint(1, 5)

            for _ in range(num_reviews):
                user = users.sample(1).iloc[0]

                # Generate review content based on product category
                review_data = self._generate_review_content(product, user)

                # Add some comments to reviews
                comments = self._generate_comments(users, review_data["created_at"])

                review_doc = {
                    "product_id": product["ID"],
                    "user_id": user["ID"],
                    "rating": review_data["rating"],
                    "title": review_data["title"],
                    "content": review_data["content"],
                    "images": review_data["images"],
                    "helpful_votes": random.randint(0, 50),
                    "verified_purchase": random.choice([True, False]),
                    "created_at": review_data["created_at"],
                    "comments": comments,
                }

                reviews_collection.insert_one(review_doc)

        print(f"Loaded reviews for {len(products)} products")

    def load_product_specs(self):
        """Load variable product specifications by category."""
        products = self.parser.parse_products()
        specs_collection = self.db.get_collection("product_specs")

        for _, product in products.iterrows():
            specs_doc = self._generate_product_specs(product)
            specs_collection.insert_one(specs_doc)

        print(f"Loaded product specs for {len(products)} products")

    def load_seller_profiles(self):
        """Load rich seller information with portfolio items."""
        sellers = self.parser.parse_sellers()
        profiles_collection = self.db.get_collection("seller_profiles")

        for _, seller in sellers.iterrows():
            profile_doc = self._generate_seller_profile(seller)
            profiles_collection.insert_one(profile_doc)

        print(f"Loaded seller profiles for {len(sellers)} sellers")

    def load_user_preferences(self):
        """Load user behavior and preference tracking."""
        users = self.parser.parse_users()
        preferences_collection = self.db.get_collection("user_preferences")

        for _, user in users.iterrows():
            preferences_doc = self._generate_user_preferences(user)
            preferences_collection.insert_one(preferences_doc)

        print(f"Loaded user preferences for {len(users)} users")

    def _generate_review_content(self, product, user) -> dict:
        """Generate realistic review content based on product."""
        category = product["CATEGORY"]
        rating = random.randint(3, 5)  # Bias towards positive reviews

        # Generate content based on category
        if "Home & Kitchen" in category:
            titles = [
                "Great quality!",
                "Perfect for my kitchen",
                "Beautiful craftsmanship",
            ]
            content = "This item exceeded my expectations. The quality is outstanding and it fits perfectly in my home."
        elif "Jewelry" in category:
            titles = ["Stunning piece!", "Beautiful design", "Love it!"]
            content = "The craftsmanship is incredible. This piece is absolutely beautiful and I receive many compliments."
        else:
            titles = ["Excellent product", "Highly recommend", "Great value"]
            content = "This is a wonderful product. The quality is great and it was exactly what I was looking for."

        # Generate random images (simulated URLs)
        images = []
        if random.choice([True, False]):
            images = [f"https://example.com/review_{random.randint(1000, 9999)}.jpg"]

        # Generate date within last year
        days_ago = random.randint(1, 365)
        created_at = datetime.now() - timedelta(days=days_ago)

        return {
            "rating": rating,
            "title": random.choice(titles),
            "content": content,
            "images": images,
            "created_at": created_at,
        }

    def _generate_comments(self, users, review_date: datetime) -> List[dict]:
        """Generate comments for reviews."""
        comments = []
        num_comments = random.randint(0, 3)

        for _ in range(num_comments):
            user = users.sample(1).iloc[0]
            comment_date = review_date + timedelta(days=random.randint(1, 30))

            comments.append(
                {
                    "user_id": user["ID"],
                    "content": random.choice(
                        [
                            "I agree!",
                            "Great review!",
                            "Thanks for sharing",
                            "This helped me decide",
                        ]
                    ),
                    "created_at": comment_date,
                }
            )

        return comments

    def _generate_product_specs(self, product) -> dict:
        """Generate product specifications based on category."""
        category = product["CATEGORY"]
        specs = {"product_id": product["ID"], "category": category}

        if "Home & Kitchen" in category:
            specs["specs"] = {
                "material": random.choice(
                    ["Acacia wood", "Bamboo", "Stainless steel", "Ceramic"]
                ),
                "dimensions": {
                    "length": random.randint(8, 20),
                    "width": random.randint(8, 20),
                    "height": random.randint(2, 8),
                    "unit": "inches",
                },
                "care_instructions": [
                    "Hand wash only",
                    "Oil regularly",
                    "Store in dry place",
                ],
                "capacity": f"{random.randint(1, 5)} liters",
            }
        elif "Jewelry" in category:
            specs["specs"] = {
                "material": random.choice(
                    ["Sterling silver", "Gold plated", "Stainless steel", "Leather"]
                ),
                "length": f"{random.randint(16, 24)} inches",
                "clasp_type": random.choice(["Lobster", "Toggle", "Magnetic"]),
                "care_instructions": [
                    "Store in jewelry box",
                    "Clean with soft cloth",
                    "Avoid chemicals",
                ],
            }
        else:
            specs["specs"] = {
                "material": "Various",
                "care_instructions": ["Follow care label", "Store properly"],
                "warranty": "30 days",
            }

        return specs

    def _generate_seller_profile(self, seller) -> dict:
        """Generate rich seller profile information."""
        return {
            "seller_id": seller["ID"],
            "name": seller["NAME"],
            "specialty": seller["SPECIALTY"],
            "rating": seller["RATING"],
            "joined": seller["JOINED"],
            "bio": f"Passionate artisan specializing in {seller['SPECIALTY']}. Creating unique, handmade pieces with love and attention to detail.",
            "location": random.choice(
                ["California", "New York", "Texas", "Florida", "Oregon"]
            ),
            "portfolio_items": random.randint(10, 50),
            "total_sales": random.randint(100, 5000),
            "response_time": f"{random.randint(1, 24)} hours",
            "shipping_policy": "Free shipping on orders over $50",
            "return_policy": "30-day returns accepted",
        }

    def _generate_user_preferences(self, user) -> dict:
        """Generate user behavior and preference tracking."""
        interests = user["INTERESTS"]

        return {
            "user_id": user["ID"],
            "interests": interests,
            "preferred_categories": random.sample(interests, min(len(interests), 3)),
            "price_range": {
                "min": random.randint(10, 50),
                "max": random.randint(100, 500),
            },
            "shopping_frequency": random.choice(["weekly", "monthly", "quarterly"]),
            "preferred_sellers": [],
            "viewed_products": [],
            "cart_abandonment_rate": random.uniform(0.1, 0.4),
            "last_active": datetime.now() - timedelta(days=random.randint(1, 30)),
        }

    def create_indexes(self):
        """Create necessary indexes for performance."""
        self.db.create_indexes()

    def load_all(self):
        """Load all document data into MongoDB."""
        print("Creating indexes...")
        self.create_indexes()

        print("Loading reviews...")
        self.load_reviews()

        print("Loading product specs...")
        self.load_product_specs()

        print("Loading seller profiles...")
        self.load_seller_profiles()

        print("Loading user preferences...")
        self.load_user_preferences()

        print("Document data loading complete!")


if __name__ == "__main__":
    loader = DocumentLoader()
    loader.load_all()
