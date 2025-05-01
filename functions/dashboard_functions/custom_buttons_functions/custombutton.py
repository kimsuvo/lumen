import sqlite3 
from functions .custom_button .database_cb1 import get_database_connection ,find_custom_button_entry 

def update_dashboard_custombutton (user_id :int ,button_name :str ,url :str )->None :
    """
    Inserts or updates the custom button for the user.
    """
    user_id_str =str (user_id )
    conn =get_database_connection (user_id_str )
    cursor =conn .cursor ()
    try :
        cursor .execute (
        "INSERT INTO custombuttons (user_id, button_name, url) VALUES (?, ?, ?)",
        (user_id_str ,button_name ,url )
        )
    except sqlite3 .IntegrityError :
        cursor .execute (
        "UPDATE custombuttons SET button_name = ?, url = ? WHERE user_id = ?",
        (button_name ,url ,user_id_str )
        )
    conn .commit ()
    conn .close ()

def remove_dashboard_custombutton (user_id :int )->None :
    """
    Removes the custom button entry for the user.
    """
    user_id_str =str (user_id )
    db_directory ="custombuttondatabase"
    existing_db_file =find_custom_button_entry (user_id_str ,db_directory )
    if existing_db_file :
        conn =sqlite3 .connect (existing_db_file )
        cursor =conn .cursor ()
        cursor .execute ("DELETE FROM custombuttons WHERE user_id = ?",(user_id_str ,))
        conn .commit ()
        conn .close ()

def fetch_dashboard_custombutton (user_id :int )->str :
    """
    Fetches the user's current custom button.
    Returns a summary string like:
      "Name: <name>, URL: <url>"
    or if no entry is found, returns:
      "No custom button set yet."
    """
    user_id_str =str (user_id )
    db_directory ="custombuttondatabase"
    existing_db_file =find_custom_button_entry (user_id_str ,db_directory )
    if existing_db_file :
        conn =sqlite3 .connect (existing_db_file )
        cursor =conn .cursor ()
        cursor .execute ("SELECT button_name, url FROM custombuttons WHERE user_id = ?",(user_id_str ,))
        result =cursor .fetchone ()
        conn .close ()
        if result :
            button_name ,url =result 
            return f"Name: {button_name }, URL: {url }"
    return "No custom button set yet."
