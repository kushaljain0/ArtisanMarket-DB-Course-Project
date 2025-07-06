"""Utilities for parsing CSV data."""

from typing import override

import pandas as pd

from src.config import DATA_DIR


class DataParser:
    @staticmethod
    def parse_products() -> pd.DataFrame:
        """Parse products CSV file."""
        df = pd.read_csv(DATA_DIR / "products.csv")
        # Convert price to float and ensure it's native Python type
        df["PRICE"] = df["PRICE"].astype(float).apply(lambda x: float(x))
        # Convert tags to list
        df["TAGS"] = df["TAGS"].apply(lambda x: x.split(","))
        return df

    @staticmethod
    def parse_users() -> pd.DataFrame:
        """Parse users CSV file."""
        df = pd.read_csv(DATA_DIR / "users.csv")
        # Convert interests to list
        df["INTERESTS"] = df["INTERESTS"].apply(lambda x: x.split(","))
        # Convert join_date to datetime
        df["JOIN_DATE"] = pd.to_datetime(df["JOIN_DATE"])
        return df

    @staticmethod
    def parse_categories() -> pd.DataFrame:
        """Parse categories CSV file."""
        return pd.read_csv(DATA_DIR / "categories.csv")

    @staticmethod
    def parse_sellers() -> pd.DataFrame:
        """Parse sellers CSV file."""
        df = pd.read_csv(DATA_DIR / "sellers.csv")
        df["RATING"] = df["RATING"].astype(float).apply(lambda x: float(x))
        df["JOINED"] = pd.to_datetime(df["JOINED"])
        return df


class CachedDataParser(DataParser):
    """Data parser with caching capability."""

    def __init__(self):
        self._cache: dict[str, pd.DataFrame] = {}

    @override
    def parse_products(self) -> pd.DataFrame:
        """Parse products with caching."""
        if "products" not in self._cache:
            self._cache["products"] = super().parse_products()
        return self._cache["products"]

    def get_data(self, data_type: str) -> pd.DataFrame:
        """Get data by type using if-elif statements for Python 3.8 compatibility."""
        if data_type == "products":
            return self.parse_products()
        elif data_type == "users":
            return self.parse_users()
        elif data_type == "categories":
            return self.parse_categories()
        elif data_type == "sellers":
            return self.parse_sellers()
        else:
            raise ValueError(f"Unknown data type: {data_type}")
