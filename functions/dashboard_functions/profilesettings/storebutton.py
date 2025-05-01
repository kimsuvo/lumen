import sqlite3 
from functions .storebutton_functions .storebutton import get_database_connection 

def update_dashboard_storebutton (user_id :int ,new_state :str )->str :
    """
    Updates the user's store button state in the buttons table.
    new_state should be either "yes" or "no".
    Returns the new state.
    """
    try :
        conn =get_database_connection ()
    except Exception as e :
        raise Exception (f"Database connection error: {e }")

    try :
        cursor =conn .cursor ()
        user_id_str =str (user_id )
        try :
            cursor .execute ("INSERT INTO buttons (user_id, storebutton) VALUES (?, ?)",(user_id_str ,new_state ))
        except sqlite3 .IntegrityError :
            cursor .execute ("UPDATE buttons SET storebutton = ? WHERE user_id = ?",(new_state ,user_id_str ))
        conn .commit ()
    except Exception as e :
        raise Exception (f"Database operation failed: {e }")
    finally :
        conn .close ()
    return new_state 

def fetch_dashboard_storebutton (user_id :int )->str :
    """
    Fetches the user's store button state.
    If the stored value is "yes", returns "Store Button ON".
    Otherwise (or if not found) returns "Store Button OFF".
    """
    try :
        conn =get_database_connection ()
    except Exception as e :
        return "Store Button OFF"

    try :
        cursor =conn .cursor ()
        user_id_str =str (user_id )
        cursor .execute ("SELECT storebutton FROM buttons WHERE user_id = ?",(user_id_str ,))
        result =cursor .fetchone ()
    except Exception :
        return "Store Button OFF"
    finally :
        conn .close ()

    if result and result [0 ]=="yes":
        return "Store Button ON"
    else :
        return "Store Button OFF"
