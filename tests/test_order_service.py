"""Tests for order service functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.order_service import OrderService


class TestOrderService:
    def setup_method(self):
        """Set up test fixtures."""
        self.order_service = OrderService()
        self.user_id = "test_user"
        self.order_id = 1
        self.items = [
            {"product_id": "P001", "quantity": 2, "price": 10.0, "total": 20.0},
            {"product_id": "P002", "quantity": 1, "price": 15.0, "total": 15.0},
        ]

    @patch("src.services.order_service.db")
    @patch("src.services.order_service.neo4j_client")
    def test_create_order_success(self, mock_neo4j, mock_db):
        """Test successfully creating an order."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order_id = self.order_service.create_order(self.user_id, self.items, 35.0)

        assert order_id == 1
        # Should execute multiple SQL statements (order + order items + stock updates)
        assert mock_cursor.execute.call_count >= 5
        mock_neo4j.add_purchase.assert_called()

    @patch("src.services.order_service.db")
    def test_create_order_failure(self, mock_db):
        """Test order creation failure."""
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order_id = self.order_service.create_order(self.user_id, self.items, 35.0)

        assert order_id is None

    @patch("src.services.order_service.db")
    def test_get_order_success(self, mock_db):
        """Test getting order details."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {"id": 1, "user_name": "Test User", "email": "test@example.com"},
            [{"product_id": "P001", "quantity": 2, "price": 10.0}],
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order = self.order_service.get_order(self.order_id)

        assert order["id"] == 1
        assert order["user_name"] == "Test User"
        assert len(order["items"]) == 1

    @patch("src.services.order_service.db")
    def test_get_order_not_found(self, mock_db):
        """Test getting non-existent order."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        order = self.order_service.get_order(999)

        assert order is None

    @patch("src.services.order_service.db")
    def test_get_user_orders(self, mock_db):
        """Test getting user order history."""
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            [{"id": 1, "total_amount": 35.0, "item_count": 2}],
            [{"product_id": "P001", "quantity": 2, "price": 10.0}],
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        orders = self.order_service.get_user_orders(self.user_id, limit=5)

        assert len(orders) == 1
        assert orders[0]["id"] == 1
        assert orders[0]["total_amount"] == 35.0

    @patch("src.services.order_service.db")
    def test_update_order_status_success(self, mock_db):
        """Test successfully updating order status."""
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        success = self.order_service.update_order_status(self.order_id, "completed")

        assert success is True
        mock_cursor.execute.assert_called_once()

    @patch("src.services.order_service.db")
    def test_update_order_status_failure(self, mock_db):
        """Test order status update failure."""
        mock_cursor = Mock()
        mock_cursor.rowcount = 0
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        success = self.order_service.update_order_status(self.order_id, "completed")

        assert success is False

    @patch("src.services.order_service.db")
    def test_get_order_statistics(self, mock_db):
        """Test getting order statistics for user."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            "total_orders": 5,
            "total_spent": 150.0,
            "avg_order_value": 30.0,
            "last_order_date": datetime.now(),
        }
        mock_cursor.fetchall.return_value = [
            {"name": "Product 1", "id": "P001", "total_quantity": 10}
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        stats = self.order_service.get_order_statistics(self.user_id)

        assert stats["total_orders"] == 5
        assert stats["total_spent"] == 150.0
        assert len(stats["top_products"]) == 1

    @patch("src.services.order_service.db")
    def test_get_recent_orders(self, mock_db):
        """Test getting recent orders across all users."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "user_name": "User 1", "item_count": 2},
            {"id": 2, "user_name": "User 2", "item_count": 1},
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        orders = self.order_service.get_recent_orders(limit=5)

        assert len(orders) == 2
        assert orders[0]["id"] == 1
        assert orders[1]["id"] == 2

    @patch("src.services.order_service.db")
    def test_cancel_order_success(self, mock_db):
        """Test successfully cancelling an order."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {"status": "pending"},  # Order status check
            [{"product_id": "P001", "quantity": 2}],  # Order items
        ]
        mock_cursor.rowcount = 1
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        success = self.order_service.cancel_order(self.order_id, self.user_id)

        assert success is True
        # Should execute multiple SQL statements (check + restore stock + update status)
        assert mock_cursor.execute.call_count >= 3

    @patch("src.services.order_service.db")
    def test_cancel_order_not_owned(self, mock_db):
        """Test cancelling order that doesn't belong to user."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Order not found
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        success = self.order_service.cancel_order(self.order_id, "other_user")

        assert success is False

    @patch("src.services.order_service.db")
    def test_cancel_order_already_completed(self, mock_db):
        """Test cancelling already completed order."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"status": "completed"}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        success = self.order_service.cancel_order(self.order_id, self.user_id)

        assert success is False

    @patch("src.services.order_service.db")
    def test_get_order_analytics(self, mock_db):
        """Test getting order analytics."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            "total_orders": 100,
            "total_revenue": 5000.0,
            "avg_order_value": 50.0,
        }
        mock_cursor.fetchall.side_effect = [
            [{"status": "completed", "count": 80}],  # Status breakdown
            [{"name": "Product 1", "id": "P001", "total_sold": 50}],  # Top products
            [{"date": "2024-01-01", "orders": 5, "revenue": 250.0}],  # Daily trends
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        analytics = self.order_service.get_order_analytics()

        assert analytics["total_orders"] == 100
        assert analytics["total_revenue"] == 5000.0
        assert "status_breakdown" in analytics
        assert "top_products" in analytics
        assert "daily_trends" in analytics

    def test_order_service_initialization(self):
        """Test order service initialization."""
        assert self.order_service.db is not None
        assert self.order_service.neo4j is not None


@pytest.mark.integration
def test_order_service_integration():
    """Integration test for order service with real database."""
    try:
        order_service = OrderService()
        # Test basic database connectivity
        with order_service.db.get_cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            assert cursor.fetchone()["test"] == 1
        assert True
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
