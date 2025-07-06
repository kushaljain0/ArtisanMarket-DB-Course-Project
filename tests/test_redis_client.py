from src.db.redis_client import redis_client


def test_add_to_cart():
    user_id = "testuser"
    product_id = "testproduct"
    redis_client.client.delete(f"cart:{user_id}")
    redis_client.add_to_cart(user_id, product_id, 2)
    cart = redis_client.client.hgetall(f"cart:{user_id}")
    assert cart[product_id] == "2"
    redis_client.add_to_cart(user_id, product_id, 1)
    cart = redis_client.client.hgetall(f"cart:{user_id}")
    assert cart[product_id] == "3"
    redis_client.client.delete(f"cart:{user_id}")


def test_rate_limit_check():
    user_id = "testuser"
    endpoint = "search"
    key = f"rate_limit:{user_id}:{endpoint}"
    redis_client.client.delete(key)
    for _ in range(1, 5):
        allowed = redis_client.rate_limit_check(user_id, endpoint)
        assert allowed
    # Simulate hitting the limit
    for _ in range(100):
        redis_client.rate_limit_check(user_id, endpoint)
    assert not redis_client.rate_limit_check(user_id, endpoint)
    redis_client.client.delete(key)
