"""
Some functions that are useful for development purposes.

Only import this module in development environments.
"""

import json
import logging
import pathlib
import httpx
from openai import AzureOpenAI
import azure.functions as func
from embeddings import fetch_embedding, fetch_computer_vision_image_embedding


def add_dev_functions(app, client: AzureOpenAI, completions_deployment, embeddings_deployment, vision_api_key, vision_endpoint, token_provider, USE_COMPUTER_VISION=False):

    @app.route(methods=["get"], auth_level="anonymous",
            route="seed_embeddings")
    def seed_embeddings(req: func.HttpRequest) -> func.HttpResponse:
        """
        If you add a new product to the data/test.json file this will fetch the embeddings and the image embedding 
        then add it to the JSON file.
        """
        diff = req.params.get('diff', False)
        # Seed the embeddings for the products in the database by calling the OpenAI API
        with open('data/test.json') as f:
            data = json.load(f)
            for product in data:
                if diff and ('embedding' not in product or product['embedding'] is None):
                    update = True
                if not diff:
                    update = True
                if update:
                    product['embedding'] = fetch_embedding(client, embeddings_deployment, product['name'] + ' ' + product['description'])
                    if USE_COMPUTER_VISION:
                        image = pathlib.Path("../html/images/products/") / product['image']
                        if image.exists():
                            product['image_embedding'] = fetch_computer_vision_image_embedding(vision_api_key=vision_api_key,
                                                                                            vision_endpoint=vision_endpoint,
                                                                                            token_provider=token_provider,
                                                                                            data=image, 
                                                                                            mimetype="image/jpeg")
                        else:
                            logging.warning(f"Image {image} does not exist")

            # Write the embeddings back to the test data
            with open('data/test.json', 'w') as f:
                json.dump(data, f)
                    
            return func.HttpResponse("Successfully seeded embeddings")


    @app.route(methods=["get"], auth_level="anonymous",
                route="seed_test_data")
    def seed_test_data(req: func.HttpRequest) -> func.HttpResponse:
        """
        Put some test data into the Azure Cosmos database
        """
        from backends.azure_cosmos import seed_test_data

        seed_test_data()
        return func.HttpResponse("Successfully seeded test data")


    @app.route(methods=["get"], auth_level="anonymous",
                    route="generate_test_data")
    def generate_test_data(req: func.HttpRequest) -> func.HttpResponse:
        """
        Generate some test data from a GPT-4 model
        """

        # Get the latest id from the database
        with open('data/test.json') as f:
            existing_data = json.load(f)
            latest_id = max([product['id'] for product in existing_data])

        new_data = []

        for _ in range(25):

            completion = client.chat.completions.create(
                model="gpt-4o", # use the GPT-4o model for generating test data because it has more parameters
                messages= [
                {
                    "role": "system",
                    "content": 
                    """  
                        Generate some test data in JSON. The data is for a clothing store. You should generate a 
                        list of products with the following fields: name, description, and price.
                        name: The name of the product, e.g. "The Ultimate Winter Jacket". Be creative with names. 
                        description: A two sentence description of the product with the color and some adjectives, e.g. "A forest green winter jacket. Ideal for autumn and winter. Made from 100% cotton."
                        price: The price of the product, e.g. 49.99
                    """
                },
                {
                    "role": "user",
                    "content": "Generate 5 items of test data for a clothing store."
                },
                {
                    "role": "assistant",
                    "content": """[
            {
                "name": "Crimson Night Hoodie",
                "description": "A warm, crimson hoodie with a kangaroo pocket and adjustable drawstrings. Great for chilly evenings.",
                "price": 39.99
            },
            {
                "name": "Chic Urban Backpack",
                "description": "A stylish black backpack perfect for city adventures. Features multiple compartments and a sleek design.",
                "price": 59.99
            },
            {
                "name": "Emerald Wave Shorts",
                "description": "Comfortable, emerald green shorts with an elastic waistband. Suitable for workouts and beachwear.",
                "price": 24.99
            },
            {
                "name": "Sapphire Breeze Jacket",
                "description": "A lightweight, sapphire blue jacket with a water-resistant finish. Perfect for windy and rainy days.",
                "price": 49.99
            },
            {
                "name": "Onyx Edge Jeans",
                "description": "Stylish, onyx black jeans with a slim fit. Made from durable denim with a hint of stretch.",
                "price": 59.99
            }
        ]"""
                },
                {
                    "role": "user",
                    "content": "Generate 5 items of test data for a clothing store."
                },
                {
                    "role": "assistant",
                    "content": """[
            {
                "name": "Ruby Flame Skirt",
                "description": "A vibrant, ruby red skirt with a flared design. Perfect for both casual and semi-formal occasions.",
                "price": 39.99
            },
            {
                "name": "Eco-Friendly T-Shirt",
                "description": "A soft, organic green cotton t-shirt that's perfect for everyday wear.",
                "price": 25.99
            },
            {
                "name": "Green and Yellow Flannel Shirt",
                "description": "A green and yellow plaid button-up shirt, perfect for posing as a coffee barista or hanging around at craft beer halls.",
                "price": 49.99
            },
            {
                "name": "Olive Green Backpack",
                "description": "A stylish olive green backpack for all your needs. Fits a 15-inch laptop. Brown leather straps and metal buckles.",
                "price": 29.99

            },
            {
                "name": "Ocean Blue Activewear Set",
                "description": "A trendy ocean blue activewear set, including a sports bra and high-waisted leggings. Designed for comfort and style during workouts.",
                "price": 54.99
            }
        ]"""
                },
                {
                    "role": "user",
                    "content": "Generate 5 items of test data for a clothing store."
                },
                ],
                max_tokens=512, # maximum number of tokens to generate
                n=1, # return only one completion
                stop=None, # stop at the end of the completion
                temperature=0.7,
                stream=False, # return the completion as a single string
            )
            data = completion.choices[0].message.content

            # check the response is JSON
            try:
                if "```json" in data:
                    # Has used markdown for JSON
                    # extract the text from the json block
                    data = data.split("```json")[1].strip().split("```")[0].strip()

                data = json.loads(data)

                # Add the latest id to the data
                for product in data:
                    latest_id += 1
                    product['id'] = latest_id
                    product['image'] = f"{latest_id}.jpeg"
            except Exception as e:
                return func.HttpResponse(f"Failed to generate test data {e}, got :" + data)
            
            new_data.extend(data)

        # Write the data to the test.json file
        with open('data/test.json', 'w') as f:
            json.dump(existing_data + new_data, f, indent=4)
        return func.HttpResponse(body=json.dumps(data))
    
    @app.route(methods=["get"], auth_level="anonymous",
                route="generate_image")
    def generate_image(req: func.HttpRequest) -> func.HttpResponse:
        """
        Generate an image for the next item in the database which doesn't have an image file
        """
        next_product = None
        with open('data/test.json') as f:
            data = json.load(f)
            for product in data:
                if 'image' in product:
                    # Does the file exist in data/images/products
                    if not (pathlib.Path("../html/images/products/") / product['image']).exists():
                        next_product = product
                        break

        if next_product is None:
            return func.HttpResponse("All images are generated")
        
        # Use dall-e 3 to generate an image
        try:
            prompt = f"A photorealistic product image with a plain for a item with this description '{next_product['description']}'. Do not include the person with the product."
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1,
                )
        except Exception as e:
            logging.error(f"Failed to generate image with prompt {prompt}")
            return func.HttpResponse(f"Failed to generate image {e}")


        image_url = response.data[0].url

        # Download the image
        image = httpx.get(image_url)

        # Write to the file
        with open(pathlib.Path("../html/images/products/") / next_product['image'], "wb") as f:
            f.write(image.content)

        return func.HttpResponse(f"Generated image for {next_product['name']}")
