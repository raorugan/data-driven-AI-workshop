#FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Install Azure Functions Core Tools
RUN apt-get update && apt-get install -y curl && \
   curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
  apt-get install -y nodejs  && \
   npm i -g azure-functions-core-tools@4 --unsafe-perm=true

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

RUN mkdir -p /data-driven-worshop

#RUN cd /data-driven-workshop

# Set the working directory
WORKDIR /data-driven-workshop

#RUN ls -ltr

# Check network connectivity
#RUN curl -I https://pypi.org

# Copy the requirements.txt file
#COPY src/api/requirements.txt  .

#RUN python -m venv .venv && \
 #   . .venv/bin/activate && \
  #  pip install --no-cache-dir -r requirements.txt



#RUN ls -ltr

COPY ./ /data-driven-workshop


#RUN ls -ltr

# Command to start the Azure Functions host
#CMD ["func", "host", "start", "--verbose"]

#CMD ["python", "-m", "azure.functions_worker"]


# Use an official lightweight image
#FROM alpine:latest

# Install SQLite3
RUN apt-get update && apt-get install -y sqlite3

# Install make and other necessary tools
RUN apt-get update && apt-get install -y make

#Install http-server
RUN npm install -g http-server

# Create a directory for the database
#RUN mkdir -p /data

# Copy the initial database file if you have one
#COPY dev.db /data/dev.db

# Set the working directory
#WORKDIR /data

# Command to keep the container running
#CMD ["sleep", "infinity"]

