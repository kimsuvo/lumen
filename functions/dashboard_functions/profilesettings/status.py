
import os 
import sqlite3 
from functions .status_functions .status_db import update_user_status 
from functions .profile_functions .userprofile_functions import get_user_status 

def update_dashboard_status (user_id :int ,new_status :str )->str :
    """
    Updates the user's status.
    - If new_status is empty or only whitespace, store an empty string.
    - Enforces a maximum of 250 characters.
    Returns the updated status.
    """
    if not new_status .strip ():
        new_status =""
    if len (new_status )>250 :
        new_status =new_status [:250 ]
    update_user_status (user_id ,new_status ,status_update_block ='no',include_last_updated =True )
    return new_status 

def fetch_dashboard_status (user_id :int )->str :
    """
    Fetches the user's current status.
    If empty, returns "-# No status set yet."
    """
    status =get_user_status (user_id )
    if not status or status .strip ()=="":
        return "-# No status set yet."
    return status 
