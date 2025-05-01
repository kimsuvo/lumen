
import os 
import re 
import sqlite3 


BLACKLISTS_DB_DIR =os .path .join ("blacklistsdatabase")
os .makedirs (BLACKLISTS_DB_DIR ,exist_ok =True )
BLACKLISTS_DB_FILES =[
os .path .join (BLACKLISTS_DB_DIR ,db_file )
for db_file in os .listdir (BLACKLISTS_DB_DIR )
if db_file .endswith (".db")
]

def user_exists_in_ban_db (user_id :int )->bool :
    """
    Check if a user exists in any banned database.
    """
    directory ="bandatabase"
    if not os .path .exists (directory ):
        return False 
    for filename in os .listdir (directory ):
        if re .match (r'^banned(_\d+)?\.db$',filename ):
            db_path =os .path .join (directory ,filename )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT 1 FROM banned WHERE user_id = ?",(user_id ,))
                if cursor .fetchone ():
                    conn .close ()
                    return True 
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error accessing {filename }: {e }")
                continue 
    return False 

def is_user_blacklisted (user_id ):
    """
    Check if a user is blacklisted by looking in all blacklist databases.
    """
    for db_path in BLACKLISTS_DB_FILES :
        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result and result [0 ].lower ()=="yes":
                return True 
        except sqlite3 .Error as e :
            print (f"Error checking blacklist in {db_path }: {e }")
    return False 
