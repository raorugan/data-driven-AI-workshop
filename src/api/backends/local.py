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
import numpy as np
from .models import Product

HAS_FTS5 = False


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
                        embedding text);""")
        
        if HAS_FTS5:
            # Create a FTS5 virtual table for full-text search
            conn.execute("""create virtual table productFtsIndex using fts5(name, description, content='products', content_rowid='id');""")
        
    # Load the test data from ../data/test.json
    with open('data/test.json') as f:
        data = json.load(f)
        for product in data:
            conn.execute("INSERT INTO products (name, description, image, price, embedding) VALUES (?, ?, ?, ?, ?)", 
                         (product['name'], 
                          product['description'], 
                          product['image'], 
                          product['price'], 
                          # Convert the embedding into a string of CSV values, this is hugely inefficient but we have 9 products
                          ','.join([str(f) for f in product['embedding']])
                          ))
        logging.info("Loaded test data into database")

    return conn

def search_products(connection: "sqlite3.Connection", query: str, fts_query: str, embedding: list[float]) -> list[Product]:
    cursor = connect(':memory:').cursor()
    
    # Do a vector search. This is sqlite and we don't have a vector index, so do a similarity on ALL of them
    cursor.execute("SELECT id, name, description, price, image, embedding FROM products");
    results = cursor.fetchall()
    distances: tuple[float, tuple[int, str, str, str]] = []
    for result in results:
        # Calculate the cosine similarity between the embeddings
        similarity = cosine_similarity(embedding, [float(a) for a in result[5].split(',')])

        # A crude cutoff filter. 
        if similarity > 0.8:
            distances.append((similarity, tuple(result[0:5])))
    
    # Sort the results by similarity, descending.
    distances = sorted(distances, key=lambda x: x[0], reverse=True)

    logging.info(f"Found {len(distances)} results with similarity > 0.8")

    # Search the productFtsIndex table for the query
    cursor = sqlite3.connect('dev.db').cursor()
    if HAS_FTS5:
        cursor.execute("SELECT id, name, description, price, image FROM productFtsIndex WHERE productFtsIndex MATCH ?", (fts_query,))
    else:
        cursor.execute("SELECT id, name, description, price, image FROM products WHERE name LIKE ? OR description LIKE ?", ('%'+query+'%', '%'+query+'%'))
    fts_results = cursor.fetchall()
    logging.info(f"Found {len(fts_results)} results from FTS5")

    # Combine the results from the FTS5 search and the vector search
    results = []
    found_ids = []
    for product in fts_results:
        results.append(Product(id=product[0], name=product[1], description=product[2], price=product[3], image=product[4], embedding=None))
        found_ids.append(product[0])

    for _, product in distances:
        if product[0] not in found_ids:
            results.append(Product(id=product[0], name=product[1], description=product[2], price=product[3], image=product[4], embedding=None))

    return results
    