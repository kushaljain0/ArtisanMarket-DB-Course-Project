"""Shopping cart management service using Redis."""

from typing import Dict, List, Optional

from src.db.redis_client import redis_client
from src.db.postgres_client import db
from src.config import CART_TTL


class CartService:
    def __init__(self):
        self.redis = redis_client
        self.cart_ttl = CART_TTL

    def get_cart(self, user_id: str) -> Dict[str, int]:
        """Get user's shopping cart."""
        cart_key = f"cart:{user_id}"
        cart_data = self.redis.client.hgetall(cart_key)

        # Convert string values to integers
        cart = {product_id: int(quantity) for product_id, quantity in cart_data.items()}
        return cart

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> bool:
        """Add item to user's cart."""
        try:
            # Verify product exists and has stock
            if not self._verify_product(product_id, quantity):
                return False

            cart_key = f"cart:{user_id}"
            self.redis.client.hincrby(cart_key, product_id, quantity)
            self.redis.client.expire(cart_key, self.cart_ttl)

            return True
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return False

    def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        """Remove item from user's cart."""
        try:
            cart_key = f"cart:{user_id}"
            self.redis.client.hdel(cart_key, product_id)
            return True
        except Exception as e:
            print(f"Error removing from cart: {e}")
            return False

    def update_cart_item(self, user_id: str, product_id: str, quantity: int) -> bool:
        """Update quantity of item in cart."""
        try:
            if quantity <= 0:
                return self.remove_from_cart(user_id, product_id)

            # Verify product exists and has stock
            if not self._verify_product(product_id, quantity):
                return False

            cart_key = f"cart:{user_id}"
            self.redis.client.hset(cart_key, product_id, quantity)
            self.redis.client.expire(cart_key, self.cart_ttl)

            return True
        except Exception as e:
            print(f"Error updating cart: {e}")
            return False

    def clear_cart(self, user_id: str) -> bool:
        """Clear user's entire cart."""
        try:
            cart_key = f"cart:{user_id}"
            self.redis.client.delete(cart_key)
            return True
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False

    def get_cart_total(self, user_id: str) -> Dict[str, float]:
        """Get cart total with product details."""
        cart = self.get_cart(user_id)
        if not cart:
            return {"total": 0.0, "items": []}

        # Get product details from PostgreSQL
        product_ids = list(cart.keys())
        products = self._get_products_by_ids(product_ids)

        total = 0.0
        items = []

        for product_id, quantity in cart.items():
            if product_id in products:
                product = products[product_id]
                item_total = product["price"] * quantity
                total += item_total

                items.append(
                    {
                        "product_id": product_id,
                        "name": product["name"],
                        "price": product["price"],
                        "quantity": quantity,
                        "total": item_total,
                    }
                )

        return {"total": total, "items": items, "item_count": len(items)}

    def convert_cart_to_order(self, user_id: str) -> Optional[int]:
        """Convert cart to order and clear cart."""
        try:
            cart_total = self.get_cart_total(user_id)
            if not cart_total["items"]:
                return None

            # Create order in PostgreSQL
            order_id = self._create_order(user_id, cart_total)

            if order_id:
                # Clear the cart after successful order creation
                self.clear_cart(user_id)
                return order_id

            return None
        except Exception as e:
            print(f"Error converting cart to order: {e}")
            return None

    def get_cart_expiry(self, user_id: str) -> Optional[int]:
        """Get time until cart expires (in seconds)."""
        try:
            cart_key = f"cart:{user_id}"
            ttl = self.redis.client.ttl(cart_key)
            return ttl if ttl > 0 else None
        except Exception:
            return None

    def _verify_product(self, product_id: str, quantity: int) -> bool:
        """Verify product exists and has sufficient stock."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, stock FROM products WHERE id = %s", (product_id,)
                )
                result = cursor.fetchone()

                if not result:
                    return False

                return result["stock"] >= quantity
        except Exception:
            return False

    def _get_products_by_ids(self, product_ids: List[str]) -> Dict[str, dict]:
        """Get product details by IDs."""
        if not product_ids:
            return {}

        try:
            with db.get_cursor() as cursor:
                # Create placeholders for IN clause
                placeholders = ",".join(["%s"] * len(product_ids))
                cursor.execute(
                    f"SELECT id, name, price FROM products WHERE id IN ({placeholders})",
                    product_ids,
                )
                results = cursor.fetchall()

                return {row["id"]: row for row in results}
        except Exception:
            return {}

    def _create_order(self, user_id: str, cart_total: dict) -> Optional[int]:
        """Create order in PostgreSQL."""
        try:
            with db.get_cursor() as cursor:
                # Create order
                cursor.execute(
                    """
                    INSERT INTO orders (user_id, total_amount, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                """,
                    (user_id, cart_total["total"]),
                )

                order_id = cursor.fetchone()["id"]

                # Create order items
                for item in cart_total["items"]:
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

                return order_id
        except Exception as e:
            print(f"Error creating order: {e}")
            return None


# Singleton instance
cart_service = CartService()
