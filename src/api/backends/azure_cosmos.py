from .models import Product
from typing import Any
import logging

def connect():
    pass

def search_products(connection: Any, query: str, fts_query: str, embedding: list[float]) -> list[Product]:
    pass