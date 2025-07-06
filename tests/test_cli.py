"""Tests for CLI functionality."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from src.cli import cli


class TestCLI:
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("src.cli.RelationalLoader")
    def test_load_relational(self, mock_loader_class):
        """Test loading relational data command."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        result = self.runner.invoke(cli, ["load", "relational"])

        assert result.exit_code == 0
        mock_loader.load_all.assert_called_once()

    @patch("src.cli.DocumentLoader")
    def test_load_documents(self, mock_loader_class):
        """Test loading document data command."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        result = self.runner.invoke(cli, ["load", "documents"])

        assert result.exit_code == 0
        mock_loader.load_all.assert_called_once()

    @patch("src.cli.GraphLoader")
    def test_load_graph(self, mock_loader_class):
        """Test loading graph data command."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        result = self.runner.invoke(cli, ["load", "graph"])

        assert result.exit_code == 0
        mock_loader.load_all.assert_called_once()

    @patch("src.cli.VectorLoader")
    def test_load_vectors(self, mock_loader_class):
        """Test loading vector embeddings command."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        result = self.runner.invoke(cli, ["load", "vectors"])

        assert result.exit_code == 0
        mock_loader.load_all.assert_called_once()

    @patch("src.cli.RelationalLoader")
    @patch("src.cli.DocumentLoader")
    @patch("src.cli.GraphLoader")
    @patch("src.cli.VectorLoader")
    def test_load_all(
        self, mock_vector_class, mock_graph_class, mock_doc_class, mock_rel_class
    ):
        """Test loading all data command."""
        mock_rel_loader = Mock()
        mock_doc_loader = Mock()
        mock_graph_loader = Mock()
        mock_vector_loader = Mock()

        mock_rel_class.return_value = mock_rel_loader
        mock_doc_class.return_value = mock_doc_loader
        mock_graph_class.return_value = mock_graph_loader
        mock_vector_class.return_value = mock_vector_loader

        result = self.runner.invoke(cli, ["load", "all"])

        assert result.exit_code == 0
        mock_rel_loader.load_all.assert_called_once()
        mock_doc_loader.load_all.assert_called_once()
        mock_graph_loader.load_all.assert_called_once()
        mock_vector_loader.load_all.assert_called_once()

    @patch("src.cli.PurchaseGenerator")
    def test_generate_purchases(self, mock_generator_class):
        """Test purchase generation command."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        result = self.runner.invoke(cli, ["generate-purchases", "--count", "50"])

        assert result.exit_code == 0
        mock_generator.generate_and_load_all.assert_called_once_with(50)

    @patch("src.cli.SearchService")
    def test_search_text(self, mock_service_class):
        """Test text search command."""
        mock_service = Mock()
        mock_service.full_text_search.return_value = [
            {"id": "P001", "name": "Test Product", "price": 25.0}
        ]
        mock_service_class.return_value = mock_service

        result = self.runner.invoke(cli, ["search", "text", "test", "--limit", "5"])

        assert result.exit_code == 0
        mock_service.full_text_search.assert_called_once_with("test", None, 5)

    @patch("src.cli.SearchService")
    def test_search_semantic(self, mock_service_class):
        """Test semantic search command."""
        mock_service = Mock()
        mock_service.semantic_search.return_value = [
            {"id": "P001", "name": "Test Product", "price": 25.0, "similarity": 0.8}
        ]
        mock_service_class.return_value = mock_service

        result = self.runner.invoke(cli, ["search", "semantic", "test", "--limit", "5"])

        assert result.exit_code == 0
        mock_service.semantic_search.assert_called_once_with("test", 5)

    @patch("src.cli.SearchService")
    def test_search_combined(self, mock_service_class):
        """Test combined search command."""
        mock_service = Mock()
        mock_service.combined_search.return_value = [
            {"id": "P001", "name": "Test Product", "price": 25.0}
        ]
        mock_service_class.return_value = mock_service

        result = self.runner.invoke(cli, ["search", "combined", "test", "--limit", "5"])

        assert result.exit_code == 0
        mock_service.combined_search.assert_called_once_with("test", None, 5)

    @patch("src.cli.cart_service")
    def test_cart_show(self, mock_cart_service):
        """Test showing cart command."""
        mock_cart_service.get_cart_total.return_value = {
            "total": 35.0,
            "items": [
                {"name": "Product 1", "price": 10.0, "quantity": 2, "total": 20.0},
                {"name": "Product 2", "price": 15.0, "quantity": 1, "total": 15.0},
            ],
        }

        result = self.runner.invoke(cli, ["cart", "show", "U001"])

        assert result.exit_code == 0
        mock_cart_service.get_cart_total.assert_called_once_with("U001")

    @patch("src.cli.cart_service")
    def test_cart_add(self, mock_cart_service):
        """Test adding to cart command."""
        mock_cart_service.add_to_cart.return_value = True

        result = self.runner.invoke(
            cli, ["cart", "add", "U001", "P001", "--quantity", "2"]
        )

        assert result.exit_code == 0
        mock_cart_service.add_to_cart.assert_called_once_with("U001", "P001", 2)

    @patch("src.cli.recommendation_service")
    def test_recommend_user(self, mock_rec_service):
        """Test user recommendations command."""
        mock_rec_service.get_user_recommendations.return_value = [
            {"product_id": "P001", "name": "Product 1", "price": 25.0, "frequency": 5}
        ]

        result = self.runner.invoke(cli, ["recommend", "user", "U001", "--limit", "5"])

        assert result.exit_code == 0
        mock_rec_service.get_user_recommendations.assert_called_once_with("U001", 5)

    @patch("src.cli.recommendation_service")
    def test_recommend_similar(self, mock_rec_service):
        """Test similar products command."""
        mock_rec_service.get_similar_products.return_value = [
            {
                "product_id": "P002",
                "name": "Similar Product",
                "price": 30.0,
                "similarity": 0.8,
            }
        ]

        result = self.runner.invoke(
            cli, ["recommend", "similar", "P001", "--limit", "5"]
        )

        assert result.exit_code == 0
        mock_rec_service.get_similar_products.assert_called_once_with("P001", 5)

    @patch("src.cli.order_service")
    def test_orders_history(self, mock_order_service):
        """Test order history command."""
        mock_order_service.get_user_orders.return_value = [
            {
                "id": 1,
                "total_amount": 35.0,
                "status": "completed",
                "item_count": 2,
                "items": [],
            }
        ]

        result = self.runner.invoke(cli, ["orders", "history", "U001", "--limit", "5"])

        assert result.exit_code == 0
        mock_order_service.get_user_orders.assert_called_once_with("U001", 5)

    @patch("src.cli.order_service")
    def test_orders_show(self, mock_order_service):
        """Test show order command."""
        mock_order_service.get_order.return_value = {
            "id": 1,
            "user_name": "Test User",
            "email": "test@example.com",
            "status": "completed",
            "total_amount": 35.0,
            "created_at": "2024-01-01",
            "items": [
                {
                    "product_name": "Product 1",
                    "quantity": 2,
                    "price": 10.0,
                    "total": 20.0,
                }
            ],
        }

        result = self.runner.invoke(cli, ["orders", "show", "1"])

        assert result.exit_code == 0
        mock_order_service.get_order.assert_called_once_with(1)

    @patch("src.cli.order_service")
    def test_orders_update_status(self, mock_order_service):
        """Test update order status command."""
        mock_order_service.update_order_status.return_value = True

        result = self.runner.invoke(cli, ["orders", "update-status", "1", "completed"])

        assert result.exit_code == 0
        mock_order_service.update_order_status.assert_called_once_with(1, "completed")

    @patch("src.cli.order_service")
    def test_orders_cancel(self, mock_order_service):
        """Test cancel order command."""
        mock_order_service.cancel_order.return_value = True

        result = self.runner.invoke(cli, ["orders", "cancel", "1", "U001"])

        assert result.exit_code == 0
        mock_order_service.cancel_order.assert_called_once_with(1, "U001")

    @patch("src.cli.order_service")
    def test_orders_stats(self, mock_order_service):
        """Test order statistics command."""
        mock_order_service.get_order_statistics.return_value = {
            "total_orders": 5,
            "total_spent": 150.0,
            "avg_order_value": 30.0,
            "last_order_date": "2024-01-01",
            "top_products": [],
        }

        result = self.runner.invoke(cli, ["orders", "stats", "U001"])

        assert result.exit_code == 0
        mock_order_service.get_order_statistics.assert_called_once_with("U001")

    @patch("src.cli.order_service")
    def test_orders_recent(self, mock_order_service):
        """Test recent orders command."""
        mock_order_service.get_recent_orders.return_value = [
            {
                "id": 1,
                "user_name": "User 1",
                "total_amount": 35.0,
                "status": "completed",
            }
        ]

        result = self.runner.invoke(cli, ["orders", "recent", "--limit", "5"])

        assert result.exit_code == 0
        mock_order_service.get_recent_orders.assert_called_once_with(5)

    @patch("src.cli.order_service")
    def test_orders_analytics(self, mock_order_service):
        """Test order analytics command."""
        mock_order_service.get_order_analytics.return_value = {
            "total_orders": 100,
            "total_revenue": 5000.0,
            "avg_order_value": 50.0,
            "status_breakdown": [],
            "top_products": [],
            "daily_trends": [],
        }

        result = self.runner.invoke(cli, ["orders", "analytics"])

        assert result.exit_code == 0
        mock_order_service.get_order_analytics.assert_called_once()

    @patch("src.cli.db")
    @patch("src.cli.mongo_client")
    @patch("src.cli.neo4j_client")
    @patch("src.cli.redis_client")
    def test_status(self, mock_redis, mock_neo4j, mock_mongo, mock_db):
        """Test system status command."""
        # Mock database connections
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"count": 10}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        mock_collection = Mock()
        mock_collection.count_documents.return_value = 25
        mock_mongo.get_collection.return_value = mock_collection

        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = {"count": 15}
        mock_session.run.return_value = mock_result
        mock_neo4j.driver.session.return_value.__enter__.return_value = mock_session

        mock_redis.client.ping.return_value = True

        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 0

    def test_help(self):
        """Test help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ArtisanMarket" in result.output

    def test_load_help(self):
        """Test load command help."""
        result = self.runner.invoke(cli, ["load", "--help"])
        assert result.exit_code == 0
        assert "Data loading commands" in result.output

    def test_search_help(self):
        """Test search command help."""
        result = self.runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search functionality commands" in result.output

    def test_cart_help(self):
        """Test cart command help."""
        result = self.runner.invoke(cli, ["cart", "--help"])
        assert result.exit_code == 0
        assert "Shopping cart commands" in result.output

    def test_recommend_help(self):
        """Test recommend command help."""
        result = self.runner.invoke(cli, ["recommend", "--help"])
        assert result.exit_code == 0
        assert "Recommendation commands" in result.output

    @patch("src.cli.RelationalLoader")
    def test_load_relational_error(self, mock_loader_class):
        """Test loading relational data with error."""
        mock_loader = Mock()
        mock_loader.load_all.side_effect = Exception("Database error")
        mock_loader_class.return_value = mock_loader

        result = self.runner.invoke(cli, ["load", "relational"])

        assert result.exit_code == 0  # Should handle error gracefully
        assert "Error loading relational data" in result.output

    @patch("src.cli.SearchService")
    def test_search_no_results(self, mock_service_class):
        """Test search with no results."""
        mock_service = Mock()
        mock_service.full_text_search.return_value = []
        mock_service_class.return_value = mock_service

        result = self.runner.invoke(cli, ["search", "text", "nonexistent"])

        assert result.exit_code == 0
        assert "No results found" in result.output

    @patch("src.cli.cart_service")
    def test_cart_empty(self, mock_cart_service):
        """Test showing empty cart."""
        mock_cart_service.get_cart_total.return_value = {"total": 0.0, "items": []}

        result = self.runner.invoke(cli, ["cart", "show", "U001"])

        assert result.exit_code == 0
        assert "Cart is empty" in result.output


@pytest.mark.integration
def test_cli_integration():
    """Integration test for CLI with real services."""
    runner = CliRunner()

    # Test help command (should always work)
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
