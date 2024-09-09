# Data Driven AI Workshop

## Query Preparation Stage

### Example prompts

```default
Generate a full-text search query for a SQL database based on a user question. 
Do not generate the whole SQL query; only generate string to go inside the MATCH parameter for FTS5 indexes. 
Use SQL boolean operators if the user has been specific about what they want to exclude in the search, only use the AND operator for nouns, for descriptive adjectives use OR.
If the question is not in English, translate the question to English before generating the search query.
If you cannot generate a search query, return just the number 0.
```

## Uploading images

### Azurite Storage Emulator

Download the [Azurite Storage Emulator](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio-code%2Cblob-storage) for VS Code. This is included in the DevContainer for this project.

### Azure Storage Accounts

Download the [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer/) and connect to the storage account.

## Common Errors

### Starting functions

```Azure.Core: Connection refused (127.0.0.1:10001). System.Net.Http: Connection refused (127.0.0.1:10001). System.Net.Sockets: Connection refused.```

This error occurs when the Azurite Storage Emulator is not running. Start the Blob Service and the Queue Service and try again.