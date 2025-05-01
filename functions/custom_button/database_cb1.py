import os 
import sqlite3 
from glob import glob 
from urllib .parse import urlparse 


def is_user_premium (user_id :int ,premium_db_dir ="premiumdatabase")->bool :
    db_files =sorted (glob (os .path .join (premium_db_dir ,"*.db")))
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


def is_user_registered (user_id :int ,credentials_db_dir ="credentialsdatabase")->bool :
    db_files =sorted (glob (os .path .join (credentials_db_dir ,"*.db")))
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



def find_custom_button_entry (user_id :str ,db_directory :str )->str :
    db_files =sorted (glob (os .path .join (db_directory ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()

            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS custombuttons (
                    user_id TEXT PRIMARY KEY,
                    button_name TEXT,
                    url TEXT
                )
            """)
            conn .commit ()
            cursor .execute ("SELECT 1 FROM custombuttons WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return db_file 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return None 




def get_database_connection (user_id :str ,db_directory ="custombuttondatabase")->sqlite3 .Connection :
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )


    existing_db_file =find_custom_button_entry (user_id ,db_directory )
    if existing_db_file :
        try :
            conn =sqlite3 .connect (existing_db_file )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS custombuttons (
                    user_id TEXT PRIMARY KEY,
                    button_name TEXT,
                    url TEXT
                )
            """)
            conn .commit ()
            return conn 
        except sqlite3 .Error as e :
            raise Exception (f"Failed to connect to database {existing_db_file }: {e }")


    db_index =1 
    while True :
        db_filename =f"button_{db_index }.db"
        db_path =os .path .join (db_directory ,db_filename )
        db_exists =os .path .exists (db_path )

        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS custombuttons (
                    user_id TEXT PRIMARY KEY,
                    button_name TEXT,
                    url TEXT
                )
            """)
            conn .commit ()
        except sqlite3 .Error as e :
            raise Exception (f"Failed to initialize database {db_path }: {e }")

        if db_exists :
            try :
                cursor .execute ("SELECT COUNT(*) FROM custombuttons")
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


def is_valid_url (url :str )->bool :
    """
    Validates the given URL to ensure it contains a valid domain.
    The URL must include a top-level domain (for example, .gg, .store, .com, .in, .uk, .co, etc.).
    """

    if not url .startswith ("http://")and not url .startswith ("https://"):
        url ="http://"+url 
    parsed =urlparse (url )
    if not parsed .netloc :
        return False 

    domain_parts =parsed .netloc .split ('.')
    if len (domain_parts )<2 :
        return False 
    tld =domain_parts [-1 ]
    if len (tld )<2 :
        return False 
    return True 


def add_or_update_custom_button (user_id :str ,button_name :str ,url :str ,db_directory ="custombuttondatabase")->None :
    """
    Adds a new custom button or updates the existing one for the given user.
    The URL is validated to ensure it contains a valid domain extension (e.g., .gg, .store, .com, .in, .uk, .co, etc.).
    """
    if not is_valid_url (url ):
        raise ValueError (
        "Invalid URL. URL must contain a valid domain extension such as .gg, .store, .com, .in, .uk, .co, etc."
        )

    conn =get_database_connection (user_id ,db_directory )
    cursor =conn .cursor ()
    try :

        cursor .execute (
        "INSERT OR REPLACE INTO custombuttons (user_id, button_name, url) VALUES (?, ?, ?)",
        (user_id ,button_name ,url )
        )
        conn .commit ()
    except sqlite3 .Error as e :
        raise Exception (f"Failed to add or update custom button for user {user_id }: {e }")
    finally :
        conn .close ()

