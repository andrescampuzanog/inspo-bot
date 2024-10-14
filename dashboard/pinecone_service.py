from pinecone import Pinecone, ServerlessSpec

# Initialize Pinecone with your API key
pc = Pinecone(api_key="")

# Define the index name and dimensions based on your embedding size
index_name = "design-elements"
dimension = 1536  # Adjust this based on your embedding size

# Get the list of existing indexes
index_list = pc.list_indexes().names()  # Get the list of index names

# Check if the index exists, and create it only if it doesn't exist
if index_name not in index_list:
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric='cosine',  # Adjust the metric if needed
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1',
        )
    )

# Connect to the index
index = pc.Index(index_name)
