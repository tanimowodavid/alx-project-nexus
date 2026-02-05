from pgvector.django import L2Distance
from products.models import Product
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


def find_relevant_products(user_query, limit=3):
    query_vector = generate_product_embedding(user_query)
    
    # We use L2Distance (Euclidean) to find the 'nearest' vectors
    results = Product.objects.annotate(
        distance=L2Distance('embedding', query_vector)
    ).order_by('distance')[:limit]
    
    context = ""
    for p in results:
        variants = p.variants.filter(is_active=True)
        v_info = ", ".join([f"{v.variant_name} (${v.price})" for v in variants])
        context += f"Product: {p.name}\nDescription: {p.description}\nOptions: {v_info}\n\n"
    
    return context
