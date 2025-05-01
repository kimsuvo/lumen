

import os 
import re 
import sqlite3 
import threading 
import random 
import string 


PENDING_FEEDBACK_DIR ='pendingfeedbackdatabase'
NUM_DATABASES =10 

PREMIUM_PENDING_FEEDBACK_DIR ='premiumpendingfeedback'
NUM_PREMIUM_DATABASES =10 

db_lock =threading .Lock ()

def user_exists_in_ban_db (user_id :int )->bool :
    """
    Checks if a user exists in any of the ban databases.
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

def is_user_premium (user_id :int )->bool :
    """
    Checks if a user is marked as premium in any premium database.
    """
    from glob import glob 
    premium_db_dir ="premiumdatabase"
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

def load_current_db_index ():
    index_file =os .path .join (PENDING_FEEDBACK_DIR ,"neg_db_index.txt")
    if os .path .exists (index_file ):
        with open (index_file ,"r")as f :
            try :
                return int (f .read ().strip ())
            except ValueError :
                return 0 
    else :
        return 0 

def save_current_db_index (index ):
    index_file =os .path .join (PENDING_FEEDBACK_DIR ,"neg_db_index.txt")
    with open (index_file ,"w")as f :
        f .write (str (index ))

def load_current_premium_db_index ():
    index_file =os .path .join (PREMIUM_PENDING_FEEDBACK_DIR ,"premium_db_index.txt")
    if os .path .exists (index_file ):
        with open (index_file ,"r")as f :
            try :
                return int (f .read ().strip ())
            except ValueError :
                return 0 
    else :
        return 0 

def save_current_premium_db_index (index ):
    index_file =os .path .join (PREMIUM_PENDING_FEEDBACK_DIR ,"premium_db_index.txt")
    with open (index_file ,"w")as f :
        f .write (str (index ))

def append_pending_feedback (feedback ,db_number ):
    """
    Appends (or replaces) a pending feedback entry into a non-premium database.
    """
    with db_lock :
        db_path =os .path .join (PENDING_FEEDBACK_DIR ,f'pending_fb_{db_number }.db')
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ('''
            INSERT OR REPLACE INTO pending_feedback 
            (vouch_number, giver_id, receiver_id, feedback, timestamp, type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''',(
        feedback ["vouch_number"],
        feedback ["giver_id"],
        feedback ["receiver_id"],
        feedback ["feedback"],
        feedback ["timestamp"],
        feedback ["type"]
        ))
        conn .commit ()
        conn .close ()

def append_premium_pending_feedback (feedback ,db_number ):
    """
    Appends (or replaces) a pending feedback entry into a premium database.
    """
    with db_lock :
        db_path =os .path .join (PREMIUM_PENDING_FEEDBACK_DIR ,f'premium_pending_fb_{db_number }.db')
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ('''
            INSERT OR REPLACE INTO pending_feedback 
            (vouch_number, giver_id, receiver_id, feedback, timestamp, type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''',(
        feedback ["vouch_number"],
        feedback ["giver_id"],
        feedback ["receiver_id"],
        feedback ["feedback"],
        feedback ["timestamp"],
        feedback ["type"]
        ))
        conn .commit ()
        conn .close ()
