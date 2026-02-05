from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_product_embedding(text):
    """
    Converts product text into a 1536-dimension vector.
    """
    if not text:
        return None
        
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    
    return response.data[0].embedding
