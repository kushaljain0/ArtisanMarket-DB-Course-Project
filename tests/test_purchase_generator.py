import pandas as pd

from src.utils.purchase_generator import PurchaseGenerator


def test_generate_purchases():
    gen = PurchaseGenerator()
    purchases = gen.generate_purchases(10)
    assert not purchases.empty
    assert {"user_id", "product_id", "quantity", "purchase_date"}.issubset(
        purchases.columns
    )
    # Check that purchase_date is after user join_date
    users = gen.users.set_index("ID")
    for _, row in purchases.iterrows():
        join_date = users.loc[row["user_id"]]["JOIN_DATE"]
        purchase_date = pd.to_datetime(row["purchase_date"])
        assert purchase_date >= join_date
