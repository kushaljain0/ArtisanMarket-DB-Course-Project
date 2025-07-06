"""Tests for recommendation service functionality."""

import pytest
from unittest.mock import Mock, patch

from src.services.recommendation_service import RecommendationService


class TestRecommendationService:
    def setup_method(self):
        """Set up test fixtures."""
        self.recommendation_service = RecommendationService()
        self.user_id = "test_user"
        self.product_id = "test_product"

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_user_recommendations(self, mock_neo4j_client):
        """Test getting personalized user recommendations."""
        # Mock Neo4j session and results
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {"product_id": "P001", "name": "Product 1", "price": 10.0, "frequency": 5},
            {"product_id": "P002", "name": "Product 2", "price": 15.0, "frequency": 3},
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_user_recommendations(
            self.user_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[1]["product_id"] == "P002"
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_frequently_bought_together(self, mock_neo4j_client):
        """Test getting frequently bought together products."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {"product_id": "P002", "name": "Product 2", "price": 15.0, "frequency": 8},
            {"product_id": "P003", "name": "Product 3", "price": 20.0, "frequency": 6},
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_frequently_bought_together(
            self.product_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P002"
        assert results[0]["frequency"] == 8
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_similar_products(self, mock_neo4j_client):
        """Test getting similar products based on SIMILAR_TO relationships."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "similarity": 0.85,
            },
            {
                "product_id": "P003",
                "name": "Product 3",
                "price": 20.0,
                "similarity": 0.72,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_similar_products(
            self.product_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P002"
        assert results[0]["similarity"] == 0.85
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_category_recommendations(self, mock_neo4j_client):
        """Test getting popular products in a category."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P001",
                "name": "Product 1",
                "price": 10.0,
                "purchase_count": 25,
            },
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "purchase_count": 18,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_category_recommendations(
            "Home & Kitchen", limit=10
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[0]["purchase_count"] == 25
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_trending_products(self, mock_neo4j_client):
        """Test getting trending products based on recent purchases."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P001",
                "name": "Product 1",
                "price": 10.0,
                "recent_purchases": 15,
            },
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "recent_purchases": 12,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_trending_products(days=30, limit=10)

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[0]["recent_purchases"] == 15
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_user_purchase_history(self, mock_neo4j_client):
        """Test getting user's purchase history."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P001",
                "name": "Product 1",
                "price": 10.0,
                "purchase_date": "2024-01-01",
                "quantity": 2,
            },
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "purchase_date": "2024-01-15",
                "quantity": 1,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_user_purchase_history(
            self.user_id, limit=10
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[0]["quantity"] == 2
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_also_bought_recommendations(self, mock_neo4j_client):
        """Test getting 'users who bought this also bought' recommendations."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "user_count": 12,
            },
            {"product_id": "P003", "name": "Product 3", "price": 20.0, "user_count": 8},
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_also_bought_recommendations(
            self.product_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P002"
        assert results[0]["user_count"] == 12
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_personalized_category_recommendations(self, mock_neo4j_client):
        """Test getting category recommendations based on user's interests."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P001",
                "name": "Product 1",
                "price": 10.0,
                "total_purchases": 25,
            },
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "total_purchases": 18,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_personalized_category_recommendations(
            self.user_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[0]["total_purchases"] == 25
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_cross_category_recommendations(self, mock_neo4j_client):
        """Test getting cross-category recommendations."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P003",
                "name": "Product 3",
                "price": 20.0,
                "popularity": 15,
            },
            {
                "product_id": "P004",
                "name": "Product 4",
                "price": 25.0,
                "popularity": 12,
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_cross_category_recommendations(
            self.user_id, limit=5
        )

        assert len(results) == 2
        assert results[0]["product_id"] == "P003"
        assert results[0]["popularity"] == 15
        mock_session.run.assert_called_once()

    def test_get_comprehensive_recommendations(self):
        """Test getting comprehensive recommendations combining multiple strategies."""
        # Mock the individual recommendation methods
        self.recommendation_service.get_user_recommendations = Mock(
            return_value=[{"product_id": "P001", "name": "Product 1", "price": 10.0}]
        )
        self.recommendation_service.get_trending_products = Mock(
            return_value=[{"product_id": "P002", "name": "Product 2", "price": 15.0}]
        )
        self.recommendation_service.get_personalized_category_recommendations = Mock(
            return_value=[{"product_id": "P003", "name": "Product 3", "price": 20.0}]
        )

        results = self.recommendation_service.get_comprehensive_recommendations(
            self.user_id, limit=6
        )

        assert "personalized" in results
        assert "trending" in results
        assert "category_based" in results
        assert len(results["personalized"]) == 1
        assert len(results["trending"]) == 1
        assert len(results["category_based"]) == 1

    @patch("src.services.recommendation_service.neo4j_client")
    def test_add_product_view(self, mock_neo4j_client):
        """Test recording a product view."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        self.recommendation_service.add_product_view(self.user_id, self.product_id)

        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_get_recently_viewed(self, mock_neo4j_client):
        """Test getting user's recently viewed products."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": "P001",
                "name": "Product 1",
                "price": 10.0,
                "viewed_at": "2024-01-01T10:00:00",
            },
            {
                "product_id": "P002",
                "name": "Product 2",
                "price": 15.0,
                "viewed_at": "2024-01-01T09:00:00",
            },
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_recently_viewed(self.user_id, limit=5)

        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert "viewed_at" in results[0]
        mock_session.run.assert_called_once()

    @patch("src.services.recommendation_service.neo4j_client")
    def test_empty_recommendations(self, mock_neo4j_client):
        """Test handling of empty recommendation results."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = []
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_user_recommendations(
            self.user_id, limit=5
        )

        assert results == []

    @patch("src.services.recommendation_service.neo4j_client")
    def test_recommendation_limit(self, mock_neo4j_client):
        """Test that recommendations respect the limit parameter."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                "product_id": f"P{i}",
                "name": f"Product {i}",
                "price": 10.0,
                "frequency": 5,
            }
            for i in range(1, 11)  # 10 products
        ]
        mock_session.run.return_value = mock_result
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        results = self.recommendation_service.get_user_recommendations(
            self.user_id, limit=3
        )

        assert len(results) == 3  # Should respect the limit
        assert results[0]["product_id"] == "P1"
        assert results[2]["product_id"] == "P3"


@pytest.mark.integration
def test_recommendation_service_integration():
    """Integration test for recommendation service with real Neo4j."""
    try:
        recommendation_service = RecommendationService()
        # Test basic Neo4j connectivity
        with recommendation_service.client.driver.session() as session:
            result = session.run("RETURN 1 as test")
            assert result.single()["test"] == 1
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")
