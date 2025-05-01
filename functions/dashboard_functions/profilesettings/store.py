

from functions .store_products .products_store_functions import get_services_and_products ,update_services_and_products 

def update_dashboard_store (user_id :int ,new_store :str )->str :
    """
    Updates the user's store.
    - If new_store is empty or only whitespace, store an empty string.
    Returns the updated store.
    """
    if not new_store .strip ():
        new_store =""
    update_services_and_products (user_id ,"store",new_store )
    return new_store 

def fetch_dashboard_store (user_id :int )->str :
    """
    Fetches the user's current store.
    If empty, returns "No store set."
    """
    store ,_ =get_services_and_products (user_id )
    if not store or store .strip ()=="":
        return "No set yet."
    return store 
