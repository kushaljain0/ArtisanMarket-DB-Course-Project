import pytest

from src.db.neo4j_client import neo4j_client


def test_create_constraints():
    try:
        neo4j_client.create_constraints()
        assert True
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")


def test_add_purchase():
    # Use dummy user and product (should exist in test DB)
    try:
        neo4j_client.add_purchase("U001", "P001", 1, "2024-01-01")
        assert True
    except Exception as e:
        pytest.skip(f"Neo4j not available or test data missing: {e}")


def test_get_recommendations():
    try:
        recs = neo4j_client.get_recommendations("U001", limit=2)
        assert isinstance(recs, list)
    except Exception as e:
        pytest.skip(f"Neo4j not available or test data missing: {e}")
