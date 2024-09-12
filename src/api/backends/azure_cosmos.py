import json
from typing import Optional
from .models import ProductWithSimilarity
import logging
import os
from azure.cosmos import exceptions, CosmosClient, PartitionKey, ContainerProxy
from azure.identity import DefaultAzureCredential

cosmos_url = os.getenv("AZURE_COSMOS_URL")
if not cosmos_url:
    logging.error("AZURE_COSMOS_URL is not set")
    raise ValueError("AZURE_COSMOS_URL is not set")

cosmos_key = os.getenv("AZURE_COSMOS_KEY", None)

DEFAULT_DATABASE_NAME = "products"
DEFAULT_CONTAINER_NAME = "products"

client: CosmosClient

if not cosmos_key:
    # assume managed identity
    credential = DefaultAzureCredential()
    client = CosmosClient(cosmos_url, credential)
else:
    client = CosmosClient(cosmos_url, cosmos_key)


vector_embedding_policy = { 
    "vectorEmbeddings": [ 
        { 
            "path": "/productImageVector", 
            "dataType": "float32", 
            "distanceFunction": "cosine", 
            "dimensions": 1024
        }, 
        { 
            "path": "/productDescriptionVector", 
            "dataType": "float32", 
            "distanceFunction": "cosine", 
            "dimensions": 1024
        } 
    ]    
}

indexing_policy = {
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [
        {
            "path": '/"_etag"/?',
            "path": "/productImageVector/*",
            "path": "/productDescriptionVector/*",
        }
    ],
    "vectorIndexes": [
        {"path": "/productImageVector", "type": "quantizedFlat"},
        {"path": "/productDescriptionVector", "type": "quantizedFlat"},
    ],
}

id_affix = "product-"

def get_container(
    database: str = DEFAULT_DATABASE_NAME, container_name: str = DEFAULT_CONTAINER_NAME
) -> ContainerProxy:
    try:
        database = client.create_database_if_not_exists(database)
        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/id"),
            indexing_policy=indexing_policy,
            vector_embedding_policy=vector_embedding_policy,
        )
        return container
    except exceptions.CosmosResourceNotFoundError:
        logging.error("Database or container not found")
        return None


def vector_search(container: ContainerProxy, embedding: list[float], embedding_field: str, top: Optional[int] = 5) -> list[ProductWithSimilarity]:
    results: list[ProductWithSimilarity] = []
    
    for item in container.query_items( 
        query=f'SELECT TOP {top} c.id, c.name, c.description, c.image, c.price, VectorDistance(c.{embedding_field},@embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.{embedding_field},@embedding)', 
        parameters=[ 
            {"name": "@embedding", "value": embedding} 
        ], 
        enable_cross_partition_query=True):
        results.append(ProductWithSimilarity(
            id=int(item['id'].replace(id_affix, "")),
            name=item['name'],
            description=item['description'],
            image=item['image'],
            price=item['price'],
            embedding=None,
            similarity=item['SimilarityScore']
        ))
    return results


def search_images(embedding: list[float]) -> list[ProductWithSimilarity]:
    container = get_container()
    if not container:
        return []
    
    return vector_search(container, embedding, "productImageVector")


def search_products(
    query: str, fts_query: str, embedding: list[float]
) -> list[ProductWithSimilarity]:
    container = get_container()
    if not container:
        return []

    results = []
    # 1. Search for products using the FTS query
    for item in container.query_items( 
        query='SELECT c.id, c.name, c.description, c.image, c.price FROM c WHERE CONTAINS(c.name, @query) OR CONTAINS(c.description, @query)', 
        parameters=[ 
            {"name": "@query", "value": fts_query} 
        ], 
        enable_cross_partition_query=True):
        results.append(ProductWithSimilarity(
            id=int(item['id'].replace(id_affix, "")),
            name=item['name'],
            description=item['description'],
            image=item['image'],
            price=item['price'],
            embedding=None,
            similarity=1.0
        ))

    # 2. Search for products using the vector search
    vector_results = vector_search(container, embedding, "productDescriptionVector")

    found_ids = [product.id for product in results]

    for product in vector_results:
        if product.id not in found_ids:
            results.append(product)
    
    return results


def seed_test_data():
    container = get_container()
    if not container:
        return

    with open("data/test.json") as f:
        data = json.load(f)
        for product in data:
            container.upsert_item(body={
                "id": f"{id_affix}{ product['id'] }", 
                "name": product["name"],
                "description": product["description"],
                "image": product["image"],
                "price": product["price"],
                "productImageVector": product.get("image_embedding", []),
                "productDescriptionVector": product.get("embedding", []),
            })
    logging.info("Loaded test data into database")
