"""
This is a local development backend for the products and product search API.

It uses sqlite and FTS5 (if available) for search.
It also uses numpy for vector similarity, BUT because SQLite doesn't do vector 
indexes it has to calculate the similarity for every product in the database.

This means the search is very slow and O(N^N), but it's good enough for development purposes.
"""

import sqlite3 
import json
import logging
from typing import Optional
import numpy as np
from .models import ProductWithSimilarity

HAS_FTS5 = False
SIMILARITY_THRESHOLD = 0.2


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Calculate the cosine similarity between two vectors
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def connect(database = 'dev.db') -> "sqlite3.Connection":
    """
    Setup the development database
    """
    global HAS_FTS5
    HAS_TABLES = False
    conn = sqlite3.connect(database)

    # If the products table exists, return the connection
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
    if cursor.fetchone():
        logging.info("Database already exists")

        # does the table have data?
        cursor.execute("SELECT * FROM products")
        if cursor.fetchone():
            logging.info("Database has data")
            return conn
        HAS_TABLES = True

    # Create a products table with the columns id, name, description, image, price and embedding
    if not HAS_TABLES:
        conn.execute("""create table products (
                        id integer primary key,
                        name text,
                        description text,
                        image text,
                        price real,
                        embedding text,
                        image_embedding text
                     );""")
        logging.info("Created products table")
        
        if HAS_FTS5:
            # Create a FTS5 virtual table for full-text search
            conn.execute("""create virtual table productFtsIndex using fts5(name, description, content='products', content_rowid='id');""")
            logging.info("Created products vtable index")

    # Load the test data from ../data/test.json
    with open('data/test.json') as f:
        data = json.load(f)
        for product in data:
            conn.execute("INSERT INTO products (name, description, image, price, embedding, image_embedding) VALUES (?, ?, ?, ?, ?, ?)", 
                         (product['name'], 
                          product['description'], 
                          product['image'], 
                          product['price'], 
                          # Convert the embedding into a string of CSV values, this is hugely inefficient but we have 9 products
                          ','.join([str(f) for f in product.get('embedding', [])]),
                          ','.join([str(f) for f in product.get('image_embedding', [])]),
                          ))
        logging.info("Loaded test data into database")

    return conn


def vector_search_products(cursor, embedding: list[float], embedding_field: Optional[str] = "embedding") -> list[ProductWithSimilarity]:
    # Do a vector search. This is sqlite and we don't have a vector index, so do a similarity on ALL of them
    cursor.execute(f"SELECT id, name, description, price, image, {embedding_field} FROM products");
    results = cursor.fetchall()
    distances: tuple[float, tuple[int, str, str, str]] = []
    for result in results:
        # Calculate the cosine similarity between the embeddings
        similarity = cosine_similarity(embedding, [float(a) for a in result[5].split(',')])

        # A crude cutoff filter. 
        if similarity > SIMILARITY_THRESHOLD:
            distances.append((similarity, tuple(result[0:5])))
    
    # Sort the results by similarity, descending.
    distances = sorted(distances, key=lambda x: x[0], reverse=True)

    logging.info(f"Found {len(distances)} results with similarity > {SIMILARITY_THRESHOLD}")

    return [ProductWithSimilarity(id=product[0], name=product[1], description=product[2], price=product[3], image=product[4], embedding=None, similarity=similarity) for similarity, product in distances]


def search_images(embedding: list[float]):
    cursor = connect(':memory:').cursor()
    return vector_search_products(cursor, embedding, 'image_embedding')


def search_products(query: str, fts_query: str, embedding: list[float]) -> list[ProductWithSimilarity]:
    cursor = connect(':memory:').cursor()

    vector_results = vector_search_products(cursor, embedding)

    # Search the productFtsIndex table for the query
    if HAS_FTS5:
        cursor.execute("SELECT id, name, description, price, image FROM productFtsIndex WHERE productFtsIndex MATCH ?", (fts_query,))
    else:
        cursor.execute("SELECT id, name, description, price, image FROM products WHERE name LIKE ? OR description LIKE ?", ('%'+query+'%', '%'+query+'%'))
    fts_results = cursor.fetchall()
    logging.info(f"Found {len(fts_results)} results from FTS5")

    # Combine the results from the FTS5 search and the vector search
    # We use a dict to get keep the results unique and ordered
    results = [ProductWithSimilarity(id=product[0], name=product[1], description=product[2], price=product[3], image=product[4], embedding=None, similarity=1) for product in fts_results]

    found_ids = [product.id for product in results]

    for product in vector_results:
        if product.id not in found_ids:
            results.append(product)

    return list(results)[:10]
    