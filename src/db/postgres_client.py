"""PostgreSQL connection and utilities."""

from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import POSTGRES_CONFIG

Base = declarative_base()


class PostgresConnection:
    def __init__(self):
        self.config = POSTGRES_CONFIG
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        if not self._engine:
            db_url = (
                f"postgresql://{self.config['user']}:{self.config['password']}@"
                f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
            self._engine = create_engine(db_url)
        return self._engine

    @property
    def session_factory(self):
        if not self._session_factory:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    @contextmanager
    def get_cursor(self):
        """Get a database cursor for raw SQL queries."""
        conn = psycopg2.connect(**self.config)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        """Create all tables in the database."""
        with self.get_cursor() as cursor:
            # Try to enable pgvector extension
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception as e:
                print(f"Warning: Could not enable pgvector extension: {e}")
                print("Vector search functionality will not be available.")

            # Categories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                );
            """)
            # Sellers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sellers (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    specialty VARCHAR(100),
                    rating FLOAT,
                    joined DATE
                );
            """)
            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    join_date DATE,
                    location VARCHAR(100),
                    interests TEXT
                );
            """)
            # Products
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category_id VARCHAR(10) REFERENCES categories(id),
                    price FLOAT,
                    seller_id VARCHAR(10) REFERENCES sellers(id),
                    description TEXT,
                    tags TEXT,
                    stock INT
                );
            """)
            # Product Embeddings (only create if pgvector is available)
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS product_embeddings (
                        product_id VARCHAR(10) PRIMARY KEY REFERENCES products(id),
                        description_embedding vector(384)
                    );
                """)
            except Exception as e:
                print(f"Warning: Could not create product_embeddings table: {e}")
                print("Vector search functionality will not be available.")

            # Orders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(10) REFERENCES users(id),
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount FLOAT,
                    status VARCHAR(20) DEFAULT 'pending'
                );
            """)

            # Order Items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id),
                    product_id VARCHAR(10) REFERENCES products(id),
                    quantity INTEGER,
                    unit_price FLOAT,
                    total_price FLOAT
                );
            """)


# Singleton instance
db = PostgresConnection()
