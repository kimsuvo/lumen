

import os 
import sqlite3 
from glob import glob 


CREDENTIALS_DB_DIR ="credentialsdatabase"
PREMIUM_DB_DIR ="premiumdatabase"
BUTTONS_DB_DIR ="buttonsdatabase"


def is_user_premium (user_id :int )->bool :
    """
    Checks if the given user_id exists in any of the premium databases.
    Returns True if found, otherwise False.
    """
    db_files =sorted (glob (os .path .join (PREMIUM_DB_DIR ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()

            cursor .execute ("SELECT 1 FROM premium WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 


def is_user_registered (user_id :int )->bool :
    """
    Checks if the given user_id is registered by searching all credential databases.
    Returns True if the user is found, otherwise False.
    """
    db_files =sorted (glob (os .path .join (CREDENTIALS_DB_DIR ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 


def get_database_connection ()->sqlite3 .Connection :
    """
    Returns a sqlite3 connection to a database file in the BUTTONS_DB_DIR.
    It finds (or creates) the first database (e.g., button_1.db, button_2.db, …)
    that has fewer than 10,000 entries in the 'buttons' table.
    If the file does not exist, it is created along with the 'buttons' table.
    """
    if not os .path .exists (BUTTONS_DB_DIR ):
        os .makedirs (BUTTONS_DB_DIR )

    db_index =1 
    while True :
        db_filename =f"button_{db_index }.db"
        db_path =os .path .join (BUTTONS_DB_DIR ,db_filename )
        db_exists =os .path .exists (db_path )

        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS buttons (
                    user_id TEXT PRIMARY KEY,
                    storebutton TEXT
                )
            """)
            conn .commit ()
        except sqlite3 .Error as e :
            raise Exception (f"Failed to initialize database {db_path }: {e }")

        if db_exists :
            try :
                cursor .execute ("SELECT COUNT(*) FROM buttons")
                (count ,)=cursor .fetchone ()
            except sqlite3 .Error as e :
                conn .close ()
                raise Exception (f"Failed to count entries in {db_path }: {e }")

            if count <10000 :
                return conn 
            else :
                conn .close ()
                db_index +=1 
        else :

            return conn 
