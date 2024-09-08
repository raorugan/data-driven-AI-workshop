# Data Driven AI Workshop


## Uploading images

### Azurite Storage Emulator

Download the [Azurite Storage Emulator](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio-code%2Cblob-storage) for VS Code. This is included in the DevContainer for this project.

### Azure Storage Accounts

Download the [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer/) and connect to the storage account.

## Common Errors

### Starting functions

```Azure.Core: Connection refused (127.0.0.1:10001). System.Net.Http: Connection refused (127.0.0.1:10001). System.Net.Sockets: Connection refused.```

This error occurs when the Azurite Storage Emulator is not running. Start the Blob Service and the Queue Service and try again.