import azure.functions as func
import logging

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
import os

azure_credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(azure_credential,
    "https://cognitiveservices.azure.com/.default")
client = AzureOpenAI(
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider
)

app = func.FunctionApp()

@app.blob_trigger(arg_name="imageblob", path="uploads",
                  connection="ImagesConnection") 
def image_trigger(imageblob: func.InputStream):
    logging.info(f"Python blob trigger function processing blob"
                f"Name: {imageblob.name}"
                f"Blob Size: {imageblob.length} bytes")


@app.route(methods=["post"], auth_level="anonymous",
                    route="search")
def search(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    query = req.params.get('query')
    if not query:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            query = req_body.get('query')

    if not query:
        return func.HttpResponse(
            "Please pass a query on the query string or in the request body",
            status_code=400
        )


    # Extract keywords using OpenAI
    ### Start of implementation
    prompt = "Extract keywords from the following text, if the user query is not in English translate the keywords to English:\n\n"

    # Get the keywords from the query
    keywords = client.completions.create(
        model="gpt-4o",
        prompt=prompt + query,
        max_tokens=50
    ).choices[0].text.strip().split("\n")

    ### End of implementation

    if query:
        return func.HttpResponse(f"Search results: {keywords}")
    else:
        return func.HttpResponse(
            "Please pass a query on the query string or in the request body",
            status_code=400
        )