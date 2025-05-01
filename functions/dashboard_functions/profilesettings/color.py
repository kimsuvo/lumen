
import sqlite3 
import re 
from functions .color_functions import db_utils 
from functions .premium_functions .premium_user_functions import is_user_premium 


predefined_colors ={
"red":"#ff0000",
"green":"#00ff00",
"yellow":"#ffff00",
"blue":"#0000ff",
"white":"#ffffff",
"black":"#000001"
}

def update_dashboard_color (user_id :int ,new_color :str )->str :
    new_color =new_color .strip ()


    if not new_color :
        color_hex =""
    else :
        premium =is_user_premium (user_id )
        if premium :

            if not re .fullmatch (r'^#[0-9a-fA-F]{6}$',new_color ):
                raise ValueError ("Invalid hex code! Please use a valid hex code (e.g., #ff0000).")
            color_hex =new_color 
        else :
            color_lower =new_color .lower ()
            if color_lower not in predefined_colors :
                raise ValueError ("Non-premium users can only choose predefined colors: red, green, yellow, blue, white, black.")
            color_hex =predefined_colors [color_lower ]

    user_id_str =str (user_id )
    user_db =db_utils .find_user_db (user_id_str )
    conn =None 
    try :
        if user_db :
            conn =sqlite3 .connect (user_db )
            c =conn .cursor ()
            c .execute ("SELECT colorlock FROM colors WHERE user_id=?",(user_id_str ,))
            result =c .fetchone ()
            if result and result [0 ].lower ()=="yes":
                raise Exception ("Your color is locked and cannot be changed.")
            c .execute ("UPDATE colors SET color=? WHERE user_id=?",(color_hex ,user_id_str ))
            conn .commit ()
        else :
            active_db =db_utils .get_active_db ()
            conn =sqlite3 .connect (active_db )
            c =conn .cursor ()
            c .execute ("INSERT INTO colors (user_id, color, colorlock) VALUES (?, ?, ?)",
            (user_id_str ,color_hex ,"no"))
            conn .commit ()
    finally :
        if conn :
            conn .close ()
    return color_hex 


def fetch_dashboard_color (user_id :int )->str :
    """
    Fetches the user's color. If not set, returns "No color set yet."
    """
    user_id_str =str (user_id )
    user_db =db_utils .find_user_db (user_id_str )
    if user_db :
        conn =sqlite3 .connect (user_db )
        try :
            c =conn .cursor ()
            c .execute ("SELECT color FROM colors WHERE user_id=?",(user_id_str ,))
            result =c .fetchone ()
            if result and result [0 ].strip ():
                return result [0 ]
            else :
                return "No color set yet."
        finally :
            conn .close ()
    return "No color set yet."
