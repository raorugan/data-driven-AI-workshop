# Data Driven AI Workshop

## Running the web server

```console
npm install -g http-server
```

```console
http-server src/html
```

## Running the API (Functions Host)

The easiest way to run the functions host is from VS Code.

Click on Run and Debug and launch the "Attach to Python Functions" launch task.

## Running the API (console)

To launch the functions host from the CLI, run the following command:

```console
func host start
```

## Making test data

```default
Can you generate 10 fictional products for a clothing store in JSON. The products have the fields name, description and price. 
```

For example:

```json
{ 
    "id": 10,
    "name": "Eco-Friendly T-Shirt",  
    "description": "A soft, organic green cotton t-shirt that's perfect for everyday wear.",  
    "price": 25.99,
    "image": "10.jpeg",
    "embedding": null
  },  
  {  
    "id": 11,
    "name": "Vintage Denim Jacket",  
    "description": "A classic denim jacket with a retro design and a modern fit.",  
    "price": 89.99,
    "image": "11.jpeg",
    "embedding": null
  }
  ```


For each item, put it into the `api/data/test.json` file and run the `seed_embeddings` function from an API call.
This will calculate the embeddings for each item that does not have an embedding field..

## Query Preparation Stage

### Example prompts

```default
Generate a full-text search query for a SQL database based on a user question. 
Do not generate the whole SQL query; only generate string to go inside the MATCH parameter for FTS5 indexes. 
Use SQL boolean operators if the user has been specific about what they want to exclude in the search, only use the AND operator for nouns, for descriptive adjectives use OR.
If the question is not in English, translate the question to English before generating the search query.
If you cannot generate a search query, return just the number 0.
```

## Adding Cosmos DB support

See [Enroll in the Vector Search Preview Feature](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#enroll-in-the-vector-search-preview-feature) for details on how to enable the Vector Search feature in Cosmos DB.



## Uploading images

### Azurite Storage Emulator

Download the [Azurite Storage Emulator](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio-code%2Cblob-storage) for VS Code. This is included in the DevContainer for this project.

### Azure Storage Accounts

Download the [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer/) and connect to the storage account.

## Common Errors

### Starting functions

```Azure.Core: Connection refused (127.0.0.1:10001). System.Net.Http: Connection refused (127.0.0.1:10001). System.Net.Sockets: Connection refused.```

This error occurs when the Azurite Storage Emulator is not running. Start the Blob Service and the Queue Service and try again.