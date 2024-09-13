import pathlib
import httpx
from urllib.parse import urljoin
import logging


def fetch_embedding(client, embeddings_deployment: str, input: str) -> list[float]:
    embedding = client.embeddings.create(
        input=input,
        model=embeddings_deployment,
        dimensions=1024,  # this is only supported in the text-embedding-3 models
    )
    return embedding.data[0].embedding


def fetch_computer_vision_image_embedding(vision_endpoint: str, vision_api_key: str, token_provider, data: bytes | pathlib.Path, mimetype: str) -> list[float]:
    if isinstance(data, pathlib.Path):
        with open(data, "rb") as f:
            data = f.read()

    endpoint = urljoin(vision_endpoint, "computervision/retrieval:vectorizeImage")
    headers = {"Content-Type": mimetype}
    params = {"api-version": "2024-02-01", "model-version": "2023-04-15"}

    if token_provider:  # Managed Identity
        headers["Authorization"] = f"Bearer " + token_provider()
    else:
        headers['Ocp-Apim-Subscription-Key'] = vision_api_key

    response = httpx.post(
            url=endpoint, params=params, headers=headers, data=data 
        )
    if response.status_code != 200:
        logging.error(f"Failed to fetch image embedding: {response.text}")

    response.raise_for_status()
    json = response.json()
    image_query_vector = json["vector"]
    return image_query_vector
