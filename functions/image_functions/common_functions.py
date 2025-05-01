

import os 
import sqlite3 


CREDENTIALS_DB_DIR ="credentialsdatabase"


os .makedirs (CREDENTIALS_DB_DIR ,exist_ok =True )

def is_user_registered (user_id :int )->bool :
    """
    Checks if the user is registered by searching through the credentials databases.
    """
    try :
        for db_file in os .listdir (CREDENTIALS_DB_DIR ):
            if db_file .endswith (".db"):
                db_path =os .path .join (CREDENTIALS_DB_DIR ,db_file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
                result =cursor .fetchone ()
                conn .close ()
                if result :
                    return True 
        return False 
    except sqlite3 .Error as e :
        print (f"Database error: {e }")
        return False 
