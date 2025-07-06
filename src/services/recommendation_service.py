"""Product recommendation service using Neo4j graph database."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.db.neo4j_client import neo4j_client


class RecommendationService:
    def __init__(self):
        self.client = neo4j_client

    def get_user_recommendations(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations for a user based on purchase history."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(other:User)-[:PURCHASED]->(rec:Product)
                WHERE NOT (u)-[:PURCHASED]->(rec)
                WITH rec, count(*) as freq
                ORDER BY freq DESC
                LIMIT $limit
                RETURN rec.id as product_id, rec.name as name, rec.price as price, freq as frequency
                """,
                user_id=user_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_frequently_bought_together(
        self, product_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get products frequently bought together with the given product."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                WHERE other.id <> $product_id
                WITH other, count(*) as freq
                ORDER BY freq DESC
                LIMIT $limit
                RETURN other.id as product_id, other.name as name, other.price as price, freq as frequency
                """,
                product_id=product_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_similar_products(
        self, product_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get products similar to the given product based on SIMILAR_TO relationships."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})-[r:SIMILAR_TO]->(similar:Product)
                RETURN similar.id as product_id, similar.name as name, similar.price as price, r.score as similarity
                ORDER BY r.score DESC
                LIMIT $limit
                """,
                product_id=product_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_category_recommendations(
        self, category_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get popular products in a specific category."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category_name})
                OPTIONAL MATCH (p)<-[:PURCHASED]-(u:User)
                WITH p, count(u) as purchase_count
                ORDER BY purchase_count DESC
                LIMIT $limit
                RETURN p.id as product_id, p.name as name, p.price as price, purchase_count
                """,
                category_name=category_name,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_trending_products(
        self, days: int = 30, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending products based on recent purchases."""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User)-[r:PURCHASED]->(p:Product)
                WHERE r.date >= $cutoff_date
                WITH p, count(*) as recent_purchases
                ORDER BY recent_purchases DESC
                LIMIT $limit
                RETURN p.id as product_id, p.name as name, p.price as price, recent_purchases
                """,
                cutoff_date=cutoff_date,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_user_purchase_history(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's purchase history."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[r:PURCHASED]->(p:Product)
                RETURN p.id as product_id, p.name as name, p.price as price, r.date as purchase_date, r.quantity
                ORDER BY r.date DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_also_bought_recommendations(
        self, product_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get 'users who bought this also bought' recommendations."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                WHERE other.id <> $product_id
                WITH other, count(DISTINCT u) as user_count
                ORDER BY user_count DESC
                LIMIT $limit
                RETURN other.id as product_id, other.name as name, other.price as price, user_count
                """,
                product_id=product_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_personalized_category_recommendations(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get category recommendations based on user's interests and purchase history."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
                WITH c, count(*) as user_purchases
                ORDER BY user_purchases DESC
                LIMIT 3
                MATCH (c)<-[:BELONGS_TO]-(popular:Product)
                OPTIONAL MATCH (popular)<-[:PURCHASED]-(buyers:User)
                WITH popular, count(buyers) as total_purchases
                ORDER BY total_purchases DESC
                LIMIT $limit
                RETURN popular.id as product_id, popular.name as name, popular.price as price, total_purchases
                """,
                user_id=user_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_cross_category_recommendations(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommendations across different categories based on user behavior."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
                WITH c, count(*) as category_purchases
                ORDER BY category_purchases DESC
                LIMIT 2
                MATCH (c)<-[:BELONGS_TO]-(p2:Product)
                WHERE NOT (u)-[:PURCHASED]->(p2)
                OPTIONAL MATCH (p2)<-[:PURCHASED]-(other_users:User)
                WITH p2, count(other_users) as popularity
                ORDER BY popularity DESC
                LIMIT $limit
                RETURN p2.id as product_id, p2.name as name, p2.price as price, popularity
                """,
                user_id=user_id,
                limit=limit,
            )
            return [record.data() for record in result]

    def get_comprehensive_recommendations(
        self, user_id: str, limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive recommendations combining multiple strategies."""
        return {
            "personalized": self.get_user_recommendations(user_id, limit // 3),
            "trending": self.get_trending_products(30, limit // 3),
            "category_based": self.get_personalized_category_recommendations(
                user_id, limit // 3
            ),
        }

    def add_product_view(self, user_id: str, product_id: str):
        """Record a product view for future recommendations."""
        with self.client.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id}), (p:Product {id: $product_id})
                MERGE (u)-[r:VIEWED]->(p)
                SET r.timestamp = datetime()
                """,
                user_id=user_id,
                product_id=product_id,
            )

    def get_recently_viewed(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's recently viewed products."""
        with self.client.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[r:VIEWED]->(p:Product)
                RETURN p.id as product_id, p.name as name, p.price as price, r.timestamp as viewed_at
                ORDER BY r.timestamp DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit,
            )
            return [record.data() for record in result]


# Singleton instance
recommendation_service = RecommendationService()
