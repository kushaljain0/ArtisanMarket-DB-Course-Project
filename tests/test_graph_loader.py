"""Tests for graph loader functionality."""

import pytest
from unittest.mock import Mock, patch

from src.loaders.graph_loader import GraphLoader


class TestGraphLoader:
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = GraphLoader()
        # Mock the parser to avoid file dependencies
        self.loader.parser = Mock()

        # Mock sample data
        self.mock_categories = Mock()
        self.mock_categories.iterrows.return_value = [
            (0, Mock(ID="C001", NAME="Home & Kitchen", DESCRIPTION="Kitchen items")),
            (1, Mock(ID="C002", NAME="Jewelry", DESCRIPTION="Jewelry items")),
        ]

        self.mock_sellers = Mock()
        self.mock_sellers.iterrows.return_value = [
            (
                0,
                Mock(
                    ID="S001",
                    NAME="Test Seller",
                    SPECIALTY="Woodworking",
                    RATING=4.5,
                    JOINED="2023-01-01",
                ),
            )
        ]

        self.mock_users = Mock()
        self.mock_users.iterrows.return_value = [
            (
                0,
                Mock(
                    ID="U001",
                    NAME="Test User",
                    EMAIL="test@example.com",
                    JOIN_DATE="2023-01-01",
                    LOCATION="Test City",
                    INTERESTS=["crafts", "kitchen"],
                ),
            )
        ]

        self.mock_products = Mock()
        self.mock_products.iterrows.return_value = [
            (
                0,
                Mock(
                    ID="P001",
                    NAME="Test Product",
                    PRICE=29.99,
                    DESCRIPTION="Test description",
                    TAGS=["wooden", "handmade"],
                    STOCK=10,
                    CATEGORY="Home & Kitchen",
                    SELLER_ID="S001",
                ),
            )
        ]

        self.loader.parser.parse_categories.return_value = self.mock_categories
        self.loader.parser.parse_sellers.return_value = self.mock_sellers
        self.loader.parser.parse_users.return_value = self.mock_users
        self.loader.parser.parse_products.return_value = self.mock_products

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_create_constraints(self, mock_neo4j_client):
        """Test constraint creation."""
        self.loader.create_constraints()
        mock_neo4j_client.create_constraints.assert_called_once()

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_load_categories(self, mock_neo4j_client):
        """Test loading categories into Neo4j."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        self.loader.load_categories()

        # Verify session.run was called for each category
        assert mock_session.run.call_count == 2

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_load_sellers(self, mock_neo4j_client):
        """Test loading sellers into Neo4j."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        self.loader.load_sellers()

        # Verify session.run was called for each seller
        assert mock_session.run.call_count == 1

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_load_users(self, mock_neo4j_client):
        """Test loading users into Neo4j."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        self.loader.load_users()

        # Verify session.run was called for each user
        assert mock_session.run.call_count == 1

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_load_products(self, mock_neo4j_client):
        """Test loading products and relationships into Neo4j."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        self.loader.load_products()

        # Should create product node and relationships
        # 1 product node + 1 BELONGS_TO relationship + 1 SOLD_BY relationship
        assert mock_session.run.call_count >= 3

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_create_similar_product_relationships(self, mock_neo4j_client):
        """Test creating similar product relationships."""
        mock_session = Mock()
        mock_neo4j_client.driver.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Mock products with overlapping tags
        mock_products = Mock()
        mock_products.iterrows.return_value = [
            (0, Mock(ID="P001", TAGS=["wooden", "handmade"])),
            (1, Mock(ID="P002", TAGS=["wooden", "kitchen"])),
            (2, Mock(ID="P003", TAGS=["metal", "modern"])),
        ]
        self.loader.parser.parse_products.return_value = mock_products

        self.loader.create_similar_product_relationships()

        # Should create relationships between products with common tags
        assert mock_session.run.called

    @patch("src.loaders.graph_loader.neo4j_client")
    def test_load_all(self, mock_neo4j_client):
        """Test loading all graph data."""
        # Mock all the individual load methods
        self.loader.create_constraints = Mock()
        self.loader.load_categories = Mock()
        self.loader.load_sellers = Mock()
        self.loader.load_users = Mock()
        self.loader.load_products = Mock()
        self.loader.create_similar_product_relationships = Mock()

        self.loader.load_all()

        # Verify all methods were called
        self.loader.create_constraints.assert_called_once()
        self.loader.load_categories.assert_called_once()
        self.loader.load_sellers.assert_called_once()
        self.loader.load_users.assert_called_once()
        self.loader.load_products.assert_called_once()
        self.loader.create_similar_product_relationships.assert_called_once()

    def test_category_mapping(self):
        """Test category name to ID mapping."""
        # Test the mapping logic used in load_products
        categories = self.mock_categories
        category_map = dict(zip(categories["NAME"], categories["ID"], strict=False))

        assert category_map["Home & Kitchen"] == "C001"
        assert category_map["Jewelry"] == "C002"


@pytest.mark.integration
def test_graph_loader_integration():
    """Integration test for graph loader with real Neo4j."""
    try:
        loader = GraphLoader()
        # This should work if Neo4j is available
        loader.create_constraints()
        assert True
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")
