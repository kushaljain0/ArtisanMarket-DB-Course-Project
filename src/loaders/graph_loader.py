"""Load data into Neo4j graph database."""

from src.db.neo4j_client import neo4j_client
from src.utils.data_parser import DataParser


class GraphLoader:
    def __init__(self):
        self.client = neo4j_client
        self.parser = DataParser()

    def create_constraints(self):
        """Create uniqueness constraints for nodes."""
        self.client.create_constraints()

    def load_categories(self):
        """Load category nodes."""
        categories = self.parser.parse_categories()

        with self.client.driver.session() as session:
            for _, category in categories.iterrows():
                session.run(
                    """
                    MERGE (c:Category {id: $id})
                    SET c.name = $name, c.description = $description
                    """,
                    id=category["ID"],
                    name=category["NAME"],
                    description=category["DESCRIPTION"],
                )

        print(f"Loaded {len(categories)} categories")

    def load_sellers(self):
        """Load seller nodes."""
        sellers = self.parser.parse_sellers()

        with self.client.driver.session() as session:
            for _, seller in sellers.iterrows():
                session.run(
                    """
                    MERGE (s:Seller {id: $id})
                    SET s.name = $name, s.specialty = $specialty, 
                        s.rating = $rating, s.joined = $joined
                    """,
                    id=seller["ID"],
                    name=seller["NAME"],
                    specialty=seller["SPECIALTY"],
                    rating=seller["RATING"],
                    joined=seller["JOINED"],
                )

        print(f"Loaded {len(sellers)} sellers")

    def load_users(self):
        """Load user nodes."""
        users = self.parser.parse_users()

        with self.client.driver.session() as session:
            for _, user in users.iterrows():
                session.run(
                    """
                    MERGE (u:User {id: $id})
                    SET u.name = $name, u.email = $email, 
                        u.join_date = $join_date, u.location = $location,
                        u.interests = $interests
                    """,
                    id=user["ID"],
                    name=user["NAME"],
                    email=user["EMAIL"],
                    join_date=user["JOIN_DATE"],
                    location=user["LOCATION"],
                    interests=",".join(user["INTERESTS"]),
                )

        print(f"Loaded {len(users)} users")

    def load_products(self):
        """Load product nodes and their relationships."""
        products = self.parser.parse_products()
        categories = self.parser.parse_categories()

        # Create category name to ID mapping
        category_map = dict(zip(categories["NAME"], categories["ID"], strict=False))

        with self.client.driver.session() as session:
            for _, product in products.iterrows():
                # Create product node
                session.run(
                    """
                    MERGE (p:Product {id: $id})
                    SET p.name = $name, p.price = $price, 
                        p.description = $description, p.tags = $tags,
                        p.stock = $stock
                    """,
                    id=product["ID"],
                    name=product["NAME"],
                    price=product["PRICE"],
                    description=product["DESCRIPTION"],
                    tags=",".join(product["TAGS"]),
                    stock=product["STOCK"],
                )

                # Create BELONGS_TO relationship with category
                category_name = product["CATEGORY"]
                category_id = category_map.get(category_name)

                if category_id:
                    session.run(
                        """
                        MATCH (p:Product {id: $product_id})
                        MATCH (c:Category {id: $category_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        product_id=product["ID"],
                        category_id=category_id,
                    )

                # Create SOLD_BY relationship with seller
                session.run(
                    """
                    MATCH (p:Product {id: $product_id})
                    MATCH (s:Seller {id: $seller_id})
                    MERGE (p)-[:SOLD_BY]->(s)
                    """,
                    product_id=product["ID"],
                    seller_id=product["SELLER_ID"],
                )

        print(f"Loaded {len(products)} products with relationships")

    def create_similar_product_relationships(self):
        """Create SIMILAR_TO relationships between products based on tags."""
        products = self.parser.parse_products()

        with self.client.driver.session() as session:
            # Find products with similar tags and create relationships
            for _, product in products.iterrows():
                product_tags = set(product["TAGS"])

                # Find other products with overlapping tags
                for _, other_product in products.iterrows():
                    if product["ID"] == other_product["ID"]:
                        continue

                    other_tags = set(other_product["TAGS"])
                    common_tags = product_tags.intersection(other_tags)

                    # Create relationship if there are common tags
                    if len(common_tags) >= 2:
                        similarity_score = len(common_tags) / len(
                            product_tags.union(other_tags)
                        )

                        session.run(
                            """
                            MATCH (p1:Product {id: $product1_id})
                            MATCH (p2:Product {id: $product2_id})
                            MERGE (p1)-[r:SIMILAR_TO]->(p2)
                            SET r.score = $score, r.common_tags = $common_tags
                            """,
                            product1_id=product["ID"],
                            product2_id=other_product["ID"],
                            score=similarity_score,
                            common_tags=list(common_tags),
                        )

        print("Created similar product relationships")

    def load_all(self):
        """Load all graph data into Neo4j."""
        print("Creating constraints...")
        self.create_constraints()

        print("Loading categories...")
        self.load_categories()

        print("Loading sellers...")
        self.load_sellers()

        print("Loading users...")
        self.load_users()

        print("Loading products and relationships...")
        self.load_products()

        print("Creating similar product relationships...")
        self.create_similar_product_relationships()

        print("Graph data loading complete!")


if __name__ == "__main__":
    loader = GraphLoader()
    loader.load_all()
