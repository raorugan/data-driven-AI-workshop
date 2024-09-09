import azure.functions as func
import logging
import json


from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI
import os

client: AzureOpenAI
DEVELOPMENT = os.getenv("DEVELOPMENT", True)

if not DEVELOPMENT:
    client = AzureOpenAI(
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_APIKEY")
    )
else:
    azure_credential = AzureCliCredential(tenant_id=os.getenv("AZURE_TENANT_ID"))
    token_provider = get_bearer_token_provider(azure_credential,
        "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider
    )
completions_deployment = os.getenv("CHAT_DEPLOYMENT_NAME", "gpt-35-turbo")

if DEVELOPMENT:
    from backends.local import connect, search_products
else:
    from backends.azure_cosmos import connect, search_products

app = func.FunctionApp()
database_connection = connect()

@app.blob_trigger(arg_name="imageblob", path="uploads",
                  connection="ImagesConnection") 
def image_trigger(imageblob: func.InputStream):
    logging.info(f"Python blob trigger function processing blob"
                f"Name: {imageblob.name}"
                f"Blob Size: {imageblob.length} bytes")


def prep_search(query: str) -> str:
    """
    Generate a full-text search query for a SQL database based on a user question.
    Use SQL boolean operators if the user has been specific about what they want to exclude in the search.
    If the question is not in English, translate the question to English before generating the search query.
    If you cannot generate a search query, return just the number 0.
    """

    ### Start of implementation
    completion = client.chat.completions.create(
        model=completions_deployment,
        messages= [
        {
            "role": "system",
            "content": 
            """  
                Generate a full-text search query for a SQL database based on a user question. 
                Do not generate the whole SQL query; only generate string to go inside the MATCH parameter for FTS5 indexes. 
                Use SQL boolean operators if the user has been specific about what they want to exclude in the search.
                If the question is not in English, translate the question to English before generating the search query.
                If you cannot generate a search query, return just the number 0.
            """
        }, 
        {
            "role": "user",
            "content": f"Generate a search query for: {query}"
        }],
        max_tokens=100, # maximum number of tokens to generate
        temperature=0.0, # no randomness, please be deterministic
        n=1, # return only one completion
        stop=None, # stop at the end of the completion
        stream=False # return the completion as a single string
    )
    search_query = completion.choices[0].message.content
    ### End of implementation
    return search_query

def fetch_embedding(input: str) -> list[float]:
    embedding = client.embeddings.create(
        input=input,
        model="embedding", # "text-embedding-ada-002"
    )
    return embedding.data[0].embedding

@app.route(methods=["post"], auth_level="anonymous",
                    route="search")
def search(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    query = req.form.get('query')
    if not query:
        return func.HttpRequest(
            "{'error': 'Please pass a query on the query string or in the request body'}",
            status_code=400
        )

    if not client: # If not using OpenAI for now, just use the query as is
        fts_query = query
        logging.info(f"Using query as is: {fts_query}")
    else:
        fts_query = prep_search(query)

    sql_results = search_products(database_connection, query, fts_query, fetch_embedding(fts_query))

    return func.HttpResponse(json.dumps({
        "keywords": fts_query,
        "results": [product.model_dump() for product in sql_results]
        }
    ))


@app.route(methods=["get"], auth_level="function",
           route="seed_embeddings")
def seed_embeddings(req: func.HttpRequest) -> func.HttpResponse:
    # Seed the embeddings for the products in the database by calling the OpenAI API
    with open('data/test.json') as f:
        data = json.load(f)
        for product in data:
            if product['embedding'] is None:
                product['embedding'] = fetch_embedding(product['name'] + ' ' + product['description'])

        # Write the embeddings back to the test data
        with open('data/test.json', 'w') as f:
            json.dump(data, f)
                
        return func.HttpResponse("Successfully seeded embeddings")