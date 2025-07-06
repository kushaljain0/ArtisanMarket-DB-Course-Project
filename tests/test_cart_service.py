"""Tests for cart service functionality."""

import pytest
from unittest.mock import Mock, patch

from src.services.cart_service import CartService


class TestCartService:
    def setup_method(self):
        """Set up test fixtures."""
        self.cart_service = CartService()
        self.user_id = "test_user"
        self.product_id = "test_product"

    @patch("src.services.cart_service.redis_client")
    def test_get_cart(self, mock_redis_client):
        """Test getting user's cart."""
        # Mock Redis response
        mock_redis_client.client.hgetall.return_value = {"P001": "2", "P002": "1"}

        cart = self.cart_service.get_cart(self.user_id)

        assert cart == {"P001": 2, "P002": 1}
        mock_redis_client.client.hgetall.assert_called_once_with(f"cart:{self.user_id}")

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_add_to_cart_success(self, mock_db, mock_redis_client):
        """Test successfully adding item to cart."""
        # Mock product verification
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": "P001", "stock": 10}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service.add_to_cart(self.user_id, self.product_id, 2)

        assert result is True
        mock_redis_client.client.hincrby.assert_called_once_with(
            f"cart:{self.user_id}", self.product_id, 2
        )
        mock_redis_client.client.expire.assert_called_once()

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_add_to_cart_insufficient_stock(self, mock_db, mock_redis_client):
        """Test adding item to cart with insufficient stock."""
        # Mock product verification - insufficient stock
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": "P001", "stock": 1}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service.add_to_cart(self.user_id, self.product_id, 5)

        assert result is False
        mock_redis_client.client.hincrby.assert_not_called()

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_add_to_cart_product_not_found(self, mock_db, mock_redis_client):
        """Test adding non-existent product to cart."""
        # Mock product verification - product not found
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service.add_to_cart(self.user_id, self.product_id, 1)

        assert result is False
        mock_redis_client.client.hincrby.assert_not_called()

    @patch("src.services.cart_service.redis_client")
    def test_remove_from_cart(self, mock_redis_client):
        """Test removing item from cart."""
        result = self.cart_service.remove_from_cart(self.user_id, self.product_id)

        assert result is True
        mock_redis_client.client.hdel.assert_called_once_with(
            f"cart:{self.user_id}", self.product_id
        )

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_update_cart_item_success(self, mock_db, mock_redis_client):
        """Test successfully updating cart item quantity."""
        # Mock product verification
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": "P001", "stock": 10}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service.update_cart_item(self.user_id, self.product_id, 3)

        assert result is True
        mock_redis_client.client.hset.assert_called_once_with(
            f"cart:{self.user_id}", self.product_id, 3
        )

    @patch("src.services.cart_service.redis_client")
    def test_update_cart_item_zero_quantity(self, mock_redis_client):
        """Test updating cart item to zero quantity (should remove)."""
        result = self.cart_service.update_cart_item(self.user_id, self.product_id, 0)

        assert result is True
        mock_redis_client.client.hdel.assert_called_once_with(
            f"cart:{self.user_id}", self.product_id
        )

    @patch("src.services.cart_service.redis_client")
    def test_clear_cart(self, mock_redis_client):
        """Test clearing entire cart."""
        result = self.cart_service.clear_cart(self.user_id)

        assert result is True
        mock_redis_client.client.delete.assert_called_once_with(f"cart:{self.user_id}")

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_get_cart_total_with_items(self, mock_db, mock_redis_client):
        """Test getting cart total with items."""
        # Mock cart contents
        mock_redis_client.client.hgetall.return_value = {"P001": "2", "P002": "1"}

        # Mock product details
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": "P001", "name": "Product 1", "price": 10.0},
            {"id": "P002", "name": "Product 2", "price": 15.0},
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        cart_total = self.cart_service.get_cart_total(self.user_id)

        assert cart_total["total"] == 35.0  # (2 * 10) + (1 * 15)
        assert len(cart_total["items"]) == 2
        assert cart_total["item_count"] == 2

    @patch("src.services.cart_service.redis_client")
    def test_get_cart_total_empty(self, mock_redis_client):
        """Test getting cart total for empty cart."""
        mock_redis_client.client.hgetall.return_value = {}

        cart_total = self.cart_service.get_cart_total(self.user_id)

        assert cart_total["total"] == 0.0
        assert cart_total["items"] == []
        assert cart_total["item_count"] == 0

    @patch("src.services.cart_service.redis_client")
    @patch("src.services.cart_service.db")
    def test_convert_cart_to_order_success(self, mock_db, mock_redis_client):
        """Test successfully converting cart to order."""
        # Mock cart contents
        mock_redis_client.client.hgetall.return_value = {"P001": "2", "P002": "1"}

        # Mock product details
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": "P001", "name": "Product 1", "price": 10.0},
            {"id": "P002", "name": "Product 2", "price": 15.0},
        ]
        mock_cursor.fetchone.return_value = {"id": 1}  # Order ID
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order_id = self.cart_service.convert_cart_to_order(self.user_id)

        assert order_id == 1
        mock_redis_client.client.delete.assert_called_once_with(f"cart:{self.user_id}")

    @patch("src.services.cart_service.redis_client")
    def test_convert_cart_to_order_empty(self, mock_redis_client):
        """Test converting empty cart to order."""
        mock_redis_client.client.hgetall.return_value = {}

        order_id = self.cart_service.convert_cart_to_order(self.user_id)

        assert order_id is None

    @patch("src.services.cart_service.redis_client")
    def test_get_cart_expiry(self, mock_redis_client):
        """Test getting cart expiry time."""
        mock_redis_client.client.ttl.return_value = 3600  # 1 hour

        expiry = self.cart_service.get_cart_expiry(self.user_id)

        assert expiry == 3600
        mock_redis_client.client.ttl.assert_called_once_with(f"cart:{self.user_id}")

    @patch("src.services.cart_service.redis_client")
    def test_get_cart_expiry_expired(self, mock_redis_client):
        """Test getting cart expiry for expired cart."""
        mock_redis_client.client.ttl.return_value = -1  # Expired

        expiry = self.cart_service.get_cart_expiry(self.user_id)

        assert expiry is None

    @patch("src.services.cart_service.db")
    def test_verify_product_success(self, mock_db):
        """Test product verification with sufficient stock."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": "P001", "stock": 10}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service._verify_product("P001", 5)

        assert result is True

    @patch("src.services.cart_service.db")
    def test_verify_product_insufficient_stock(self, mock_db):
        """Test product verification with insufficient stock."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": "P001", "stock": 3}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service._verify_product("P001", 5)

        assert result is False

    @patch("src.services.cart_service.db")
    def test_verify_product_not_found(self, mock_db):
        """Test product verification for non-existent product."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        result = self.cart_service._verify_product("NONEXISTENT", 1)

        assert result is False

    @patch("src.services.cart_service.db")
    def test_get_products_by_ids(self, mock_db):
        """Test getting product details by IDs."""
        product_ids = ["P001", "P002"]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": "P001", "name": "Product 1", "price": 10.0},
            {"id": "P002", "name": "Product 2", "price": 15.0},
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        products = self.cart_service._get_products_by_ids(product_ids)

        assert len(products) == 2
        assert products["P001"]["name"] == "Product 1"
        assert products["P002"]["name"] == "Product 2"

    @patch("src.services.cart_service.db")
    def test_get_products_by_ids_empty(self, mock_db):
        """Test getting product details for empty list."""
        products = self.cart_service._get_products_by_ids([])

        assert products == {}

    @patch("src.services.cart_service.db")
    def test_create_order(self, mock_db):
        """Test creating order in PostgreSQL."""
        cart_total = {
            "total": 35.0,
            "items": [
                {"product_id": "P001", "quantity": 2, "price": 10.0, "total": 20.0},
                {"product_id": "P002", "quantity": 1, "price": 15.0, "total": 15.0},
            ],
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 1}  # Order ID
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order_id = self.cart_service._create_order(self.user_id, cart_total)

        assert order_id == 1
        # Should execute multiple SQL statements (order + order items + stock updates)
        assert mock_cursor.execute.call_count >= 5


@pytest.mark.integration
def test_cart_service_integration():
    """Integration test for cart service with real Redis."""
    try:
        cart_service = CartService()
        # Test basic Redis connectivity
        cart_service.redis.client.ping()
        assert True
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
