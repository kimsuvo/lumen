from functions .store_products .products_store_functions import get_services_and_products 

def fetch_dashboard_products (user_id :int )->str :
    """
    Fetches the user's current products.
    Returns a multi‐line string with each product (or "No set yet." if empty).
    """
    _ ,products =get_services_and_products (user_id )
    if not products :
        return "No set yet."
    return "\n".join (products )
