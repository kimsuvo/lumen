
import os 
import sqlite3 
from glob import glob 

def is_user_premium (user_id :int )->bool :
    """
    Checks if the given user is marked as premium by scanning the premium database(s).
    """
    premium_db_dir ="premiumdatabase"
    db_files =sorted (glob (f"{premium_db_dir }/*.db"))
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
