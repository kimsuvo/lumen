import sqlite3 
import os 
from glob import glob 

CRED_DIR ="credentialsdatabase"
PREMIUM_DB_DIR ="premiumdatabase"

def is_user_registered (user_id ):
    """
    Checks if the user is registered across all credentials databases.
    """
    if not os .path .exists (CRED_DIR ):
        return False 
    for db_file in os .listdir (CRED_DIR ):
        if db_file .endswith (".db"):
            conn =sqlite3 .connect (os .path .join (CRED_DIR ,db_file ))
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            if cursor .fetchone ():
                conn .close ()
                return True 
            conn .close ()
    return False 

def is_user_premium (user_id :int )->bool :
    """
    Checks if the user is premium by scanning the premium databases.
    """
    db_files =sorted (glob (f"{PREMIUM_DB_DIR }/*.db"))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM premium WHERE user_id = ?",(str (user_id ),))
            if cursor .fetchone ():
                conn .close ()
                return True 
            conn .close ()
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 
