"""Order service for managing orders and order history."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.db.postgres_client import db
from src.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing orders and order processing."""

    def __init__(self):
        self.db = db
        self.neo4j = neo4j_client

    def create_order(
        self, user_id: str, items: List[Dict], total_amount: float
    ) -> Optional[int]:
        """Create a new order in PostgreSQL."""
        try:
            with self.db.get_cursor() as cursor:
                # Create order
                cursor.execute(
                    """
                    INSERT INTO orders (user_id, total_amount, status, order_date)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """,
                    (user_id, total_amount, "pending", datetime.now()),
                )

                order_id = cursor.fetchone()["id"]

                # Create order items
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (
                            order_id,
                            item["product_id"],
                            item["quantity"],
                            item["price"],
                            item["total"],
                        ),
                    )

                    # Update product stock
                    cursor.execute(
                        """
                        UPDATE products 
                        SET stock = stock - %s 
                        WHERE id = %s
                    """,
                        (item["quantity"], item["product_id"]),
                    )

                # Add purchase to Neo4j for recommendations
                for item in items:
                    self.neo4j.add_purchase(
                        user_id,
                        item["product_id"],
                        item["quantity"],
                        datetime.now().strftime("%Y-%m-%d"),
                    )

                logger.info(f"Order {order_id} created for user {user_id}")
                return order_id

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None

    def get_order(self, order_id: int) -> Optional[Dict]:
        """Get order details by ID."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT o.*, u.name as user_name, u.email
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    WHERE o.id = %s
                """,
                    (order_id,),
                )

                order = cursor.fetchone()
                if not order:
                    return None

                # Get order items
                cursor.execute(
                    """
                    SELECT oi.*, p.name as product_name, p.description
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """,
                    (order_id,),
                )

                items = cursor.fetchall()
                order["items"] = items

                # Add created_at field for compatibility (use order_date)
                order["created_at"] = order["order_date"]

                return order

        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None

    def get_user_orders(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get order history for a user."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT o.*, 
                           COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.user_id = %s
                    GROUP BY o.id
                    ORDER BY o.order_date DESC
                    LIMIT %s
                """,
                    (user_id, limit),
                )

                orders = cursor.fetchall()

                # Get items for each order
                for order in orders:
                    cursor.execute(
                        """
                        SELECT oi.*, p.name as product_name
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.id
                        WHERE oi.order_id = %s
                    """,
                        (order["id"],),
                    )

                    order["items"] = cursor.fetchall()

                return orders

        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE orders 
                    SET status = %s
                    WHERE id = %s
                """,
                    (status, order_id),
                )

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            return False

    def get_order_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get order statistics for a user."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_amount) as total_spent,
                        AVG(total_amount) as avg_order_value,
                        MAX(order_date) as last_order_date
                    FROM orders 
                    WHERE user_id = %s AND status = 'completed'
                """,
                    (user_id,),
                )

                stats = cursor.fetchone()

                # Get most ordered products
                cursor.execute(
                    """
                    SELECT p.name, p.id, SUM(oi.quantity) as total_quantity
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.user_id = %s AND o.status = 'completed'
                    GROUP BY p.id, p.name
                    ORDER BY total_quantity DESC
                    LIMIT 5
                """,
                    (user_id,),
                )

                stats["top_products"] = cursor.fetchall()

                return stats

        except Exception as e:
            logger.error(f"Error getting order statistics for user {user_id}: {e}")
            return {}

    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        """Get recent orders across all users."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT o.*, u.name as user_name,
                           COUNT(oi.id) as item_count
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    GROUP BY o.id, u.name
                    ORDER BY o.order_date DESC
                    LIMIT %s
                """,
                    (limit,),
                )

                return cursor.fetchall()

        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []

    def cancel_order(self, order_id: int, user_id: str) -> bool:
        """Cancel an order and restore stock."""
        try:
            with self.db.get_cursor() as cursor:
                # Check if order belongs to user and is cancellable
                cursor.execute(
                    """
                    SELECT status FROM orders 
                    WHERE id = %s AND user_id = %s
                """,
                    (order_id, user_id),
                )

                order = cursor.fetchone()
                if not order or order["status"] not in ["pending", "processing"]:
                    return False

                # Get order items to restore stock
                cursor.execute(
                    """
                    SELECT product_id, quantity FROM order_items 
                    WHERE order_id = %s
                """,
                    (order_id,),
                )

                items = cursor.fetchall()

                # Restore stock
                for item in items:
                    cursor.execute(
                        """
                        UPDATE products 
                        SET stock = stock + %s 
                        WHERE id = %s
                    """,
                        (item["quantity"], item["product_id"]),
                    )

                # Update order status
                cursor.execute(
                    """
                    UPDATE orders 
                    SET status = 'cancelled'
                    WHERE id = %s
                """,
                    (order_id,),
                )

                logger.info(f"Order {order_id} cancelled by user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_order_analytics(self) -> Dict[str, Any]:
        """Get order analytics for admin dashboard."""
        try:
            with self.db.get_cursor() as cursor:
                # Total orders and revenue
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_order_value
                    FROM orders 
                    WHERE status = 'completed'
                """)

                analytics = cursor.fetchone()

                # Orders by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM orders 
                    GROUP BY status
                """)

                analytics["status_breakdown"] = cursor.fetchall()

                # Top selling products
                cursor.execute("""
                    SELECT p.name, p.id, SUM(oi.quantity) as total_sold
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.status = 'completed'
                    GROUP BY p.id, p.name
                    ORDER BY total_sold DESC
                    LIMIT 10
                """)

                analytics["top_products"] = cursor.fetchall()

                # Daily order trends (last 30 days)
                cursor.execute("""
                    SELECT DATE(order_date) as date, COUNT(*) as orders, SUM(total_amount) as revenue
                    FROM orders 
                    WHERE order_date >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(order_date)
                    ORDER BY date DESC
                """)

                analytics["daily_trends"] = cursor.fetchall()

                return analytics

        except Exception as e:
            logger.error(f"Error getting order analytics: {e}")
            return {}


# Global order service instance
order_service = OrderService()
