

from functions .premium_functions .premium_activate import user_has_premium 

def fetch_dashboard_premium (user_id :int )->str :
    """
    Returns "Premium Active" if the user has premium; otherwise, returns "Premium Not Activated".
    """
    return "Premium Active"if user_has_premium (str (user_id ))else "Premium Not Activated"
