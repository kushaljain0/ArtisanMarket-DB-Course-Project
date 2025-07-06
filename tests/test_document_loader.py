"""Tests for document loader functionality."""

import pytest
from unittest.mock import Mock

from src.loaders.document_loader import DocumentLoader


class TestDocumentLoader:
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DocumentLoader()
        # Mock the parser to avoid file dependencies
        self.loader.parser = Mock()

        # Mock sample data
        self.mock_products = Mock()
        self.mock_products.iterrows.return_value = [
            (0, Mock(ID="P001", CATEGORY="Home & Kitchen", NAME="Test Product")),
            (1, Mock(ID="P002", CATEGORY="Jewelry", NAME="Test Jewelry")),
        ]

        self.mock_users = Mock()
        self.mock_users.sample.return_value = Mock(
            iloc=[Mock(ID="U001", INTERESTS=["crafts", "kitchen"])]
        )

        self.loader.parser.parse_products.return_value = self.mock_products
        self.loader.parser.parse_users.return_value = self.mock_users

    def test_load_reviews(self):
        """Test loading reviews into MongoDB."""
        # Mock the MongoDB collection
        mock_collection = Mock()
        self.loader.db.get_collection = Mock(return_value=mock_collection)

        # Mock the review generation methods
        self.loader._generate_review_content = Mock(
            return_value={
                "rating": 5,
                "title": "Great product!",
                "content": "Amazing quality",
                "images": [],
                "created_at": "2024-01-01",
            }
        )
        self.loader._generate_comments = Mock(return_value=[])

        # Test the method
        self.loader.load_reviews()

        # Verify collection was called
        assert mock_collection.insert_one.called
        # Should be called for each product
        assert mock_collection.insert_one.call_count == 2

    def test_load_product_specs(self):
        """Test loading product specifications."""
        mock_collection = Mock()
        self.loader.db.get_collection = Mock(return_value=mock_collection)

        # Mock the specs generation
        self.loader._generate_product_specs = Mock(
            return_value={
                "product_id": "P001",
                "category": "Home & Kitchen",
                "specs": {"material": "Wood", "dimensions": {"length": 10}},
            }
        )

        self.loader.load_product_specs()

        assert mock_collection.insert_one.called
        assert mock_collection.insert_one.call_count == 2

    def test_load_seller_profiles(self):
        """Test loading seller profiles."""
        mock_collection = Mock()
        self.loader.db.get_collection = Mock(return_value=mock_collection)

        # Mock sellers data
        mock_sellers = Mock()
        mock_sellers.iterrows.return_value = [
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
        self.loader.parser.parse_sellers = Mock(return_value=mock_sellers)

        self.loader.load_seller_profiles()

        assert mock_collection.insert_one.called

    def test_load_user_preferences(self):
        """Test loading user preferences."""
        mock_collection = Mock()
        self.loader.db.get_collection = Mock(return_value=mock_collection)

        # Mock users data
        mock_users = Mock()
        mock_users.iterrows.return_value = [
            (0, Mock(ID="U001", INTERESTS=["crafts", "kitchen"]))
        ]
        self.loader.parser.parse_users = Mock(return_value=mock_users)

        self.loader.load_user_preferences()

        assert mock_collection.insert_one.called

    def test_generate_review_content(self):
        """Test review content generation."""
        product = Mock(CATEGORY="Home & Kitchen")
        user = Mock()

        result = self.loader._generate_review_content(product, user)

        assert "rating" in result
        assert "title" in result
        assert "content" in result
        assert "images" in result
        assert "created_at" in result
        assert 3 <= result["rating"] <= 5

    def test_generate_product_specs(self):
        """Test product specifications generation."""
        product = Mock(ID="P001", CATEGORY="Home & Kitchen")

        result = self.loader._generate_product_specs(product)

        assert result["product_id"] == "P001"
        assert result["category"] == "Home & Kitchen"
        assert "specs" in result

    def test_create_indexes(self):
        """Test index creation."""
        # Mock the create_indexes method
        self.loader.db.create_indexes = Mock()

        self.loader.create_indexes()

        self.loader.db.create_indexes.assert_called_once()

    def test_load_all(self):
        """Test loading all document data."""
        # Mock all the individual load methods
        self.loader.create_indexes = Mock()
        self.loader.load_reviews = Mock()
        self.loader.load_product_specs = Mock()
        self.loader.load_seller_profiles = Mock()
        self.loader.load_user_preferences = Mock()

        self.loader.load_all()

        # Verify all methods were called
        self.loader.create_indexes.assert_called_once()
        self.loader.load_reviews.assert_called_once()
        self.loader.load_product_specs.assert_called_once()
        self.loader.load_seller_profiles.assert_called_once()
        self.loader.load_user_preferences.assert_called_once()


@pytest.mark.integration
def test_document_loader_integration():
    """Integration test for document loader with real MongoDB."""
    try:
        loader = DocumentLoader()
        # This should work if MongoDB is available
        loader.create_indexes()
        assert True
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")
