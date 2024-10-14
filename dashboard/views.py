from django.shortcuts import render, redirect
from django.contrib import messages  # To display messages to the user

# Import models
from .models import Resource, Tag

from openai import OpenAI

from pydantic import BaseModel

import base64

from .pinecone_service import index  # Import the initialized Pinecone index

import numpy as np

import json

client = OpenAI(
  organization='',
  api_key="",
)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


class tags(BaseModel):
    tags: list[str]


def upload(request):
    
    if request.method == "GET":
        
        return render (request, "upload.html")
    
    
    else:
        # Check if a file is in the request
        if "file" not in request.FILES:
            messages.error(request, "No file selected for upload.")  # Send an error message
            return render(request, "upload.html")  # Re-render the form with the message

        # If the file exists, proceed with handling it
        file = request.FILES["file"]
        
        # Create a new Resource object
        resource = Resource(resource=file)
        resource.save()
        
        path_to_image = resource.resource.path
        
        base64_image = encode_image(path_to_image)
        
        
        
        completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Give me tags for this image, up to 50 different tags. This tags should ONLY describe the image design elements, just tag what the image includes dont invent design elements or imagine elements, just what is actually in the image, you dont have to max out the 50 tags if its not necessary. Make sure all the tags are in lowercase."},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
                },
            ],
            }
        ],
        response_format=tags
        )
        
        data_string = completion.choices[0].message.content
        
        data_json = json.loads(data_string)

        list = data_json['tags']
        
        for tag in list:
            # Create a tag object with its embeddings
            response = client.embeddings.create(input=tag, model="text-embedding-3-small")
            embedding = response.data[0].embedding
            Tag.objects.create(resource=resource, tag=tag, embedding=embedding)
            # Use the Pinecone index to upsert embeddings
            index.upsert([{
                'id': f'{resource.id}_{tag}',
                'values': embedding,
                'metadata': {'resource_id': resource.id, 'tag': tag}
            }])        
        
        messages.success(request, "File uploaded and tags generated successfully!")
    
        return redirect("upload")


def resources(request):
    
    if request.method == "GET":
        
        resources = Resource.objects.all()
        context = {"resources": resources}
        
        return render(request, "resources.html", context)
    
    
    return render(request, "resources.html")


def search(request):
    if request.method == "POST":
        # Get the user's search query and convert it to lowercase
        query = request.POST.get('query').lower()

        if not query:
            messages.error(request, "Please enter a search query.")
            return render(request, "search.html")

        # Step 1: Exact Match or Partial Match Search
        # Using __icontains for partial match
        matching_tags = Tag.objects.filter(tag__icontains=query)  # Case-insensitive partial match
        matching_resource_ids = list(matching_tags.values_list('resource_id', flat=True))

        # Step 2: Initialize list of embeddings for the query and any matching tags
        embeddings_to_search = []

        # Step 3: Convert the query to an embedding using OpenAI (for semantic search)
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"  # Ensure the same model is used for consistency
        )
        query_embedding = response.data[0].embedding
        embeddings_to_search.append(query_embedding)  # Add the query embedding to search

        # Step 4: Perform a semantic search in Pinecone using the query embedding
        semantic_search_results = index.query(
            vector=query_embedding,
            top_k=5,  # Retrieve the top 10 most similar results
            include_metadata=True  # Include metadata (e.g., resource_id)
        )
        
        # Extract resource IDs from semantic search results
        semantic_match_resource_ids = [result['metadata']['resource_id'] for result in semantic_search_results['matches']]

        # Step 5: Combine exact match and semantic search resource IDs, avoiding duplicates
        combined_resource_ids = list(set(matching_resource_ids + semantic_match_resource_ids))  # Remove duplicates

        # Step 6: Retrieve the corresponding Resource objects from the Django database
        resources = Resource.objects.filter(id__in=combined_resource_ids)

        # Step 7: Pass the results to the template
        context = {
            "resources": resources, 
            "query": query, 
            "exact_match_ids": matching_resource_ids,  # IDs from partial/exact match for frontend differentiation
            "semantic_match_ids": semantic_match_resource_ids  # IDs from semantic match for frontend differentiation
        }
        return render(request, "search.html", context)

    # If it's a GET request, just render the search form
    return render(request, "search.html")