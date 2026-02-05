from pgvector.django import L2Distance
from products.models import Product
from products.utils import generate_product_embedding


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
