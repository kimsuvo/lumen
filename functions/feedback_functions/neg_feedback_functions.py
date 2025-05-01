

import os 
import sqlite3 
import re 
import random 
import string 
import unicodedata 
from datetime import datetime ,timedelta 
import pytz 
import threading 


from functions .feedback_functions .negfb_database_functions import PENDING_FEEDBACK_DIR ,NUM_DATABASES 


last_vouch_time ={}
INDIA_TZ =pytz .timezone ("Asia/Kolkata")

def can_vouch_again (user_id ):
    """
    Returns True if at least 10 seconds have passed since the user last gave feedback.
    """
    now =datetime .now (INDIA_TZ )
    last_time =last_vouch_time .get (user_id )
    if last_time and now -last_time <timedelta (seconds =10 ):
        return False 
    last_vouch_time [user_id ]=now 
    return True 


BLACKLISTS_DIR ='blacklistsdatabase'
blacklists_lock =threading .Lock ()

def is_user_blacklisted (user_id ):
    with blacklists_lock :
        db_files =sorted (
        [f for f in os .listdir (BLACKLISTS_DIR )if re .match (r'^blacklists_(\d+)\.db$',f )],
        key =lambda x :int (re .search (r'blacklists_(\d+)\.db$',x ).group (1 ))
        )
        for db_file in db_files :
            db_path =os .path .join (BLACKLISTS_DIR ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(str (user_id ),))
                result =cursor .fetchone ()
                conn .close ()
                if result and result [0 ].lower ()=="yes":
                    return True 
            except Exception as e :
                print (f"Error accessing {db_path }: {e }")
                continue 
    return False 

def load_pending_feedback ():
    """
    Loads all pending feedback entries from non-premium databases.
    """
    pending_feedbacks =[]
    for i in range (1 ,NUM_DATABASES +1 ):
        db_path =os .path .join (PENDING_FEEDBACK_DIR ,f'pending_fb_{i }.db')
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT * FROM pending_feedback")
        rows =cursor .fetchall ()
        for row in rows :
            feedback ={
            "vouch_number":row [0 ],
            "giver_id":row [1 ],
            "receiver_id":row [2 ],
            "feedback":row [3 ],
            "timestamp":row [4 ],
            "type":row [5 ]
            }
            pending_feedbacks .append (feedback )
        conn .close ()
    return pending_feedbacks 

def save_pending_feedback (pending_feedbacks ):
    """
    Clears all non-premium pending feedback tables and redistributes the feedback entries.
    """
    from functions .feedback_functions .negfb_database_functions import NUM_DATABASES ,PENDING_FEEDBACK_DIR 

    for i in range (1 ,NUM_DATABASES +1 ):
        db_path =os .path .join (PENDING_FEEDBACK_DIR ,f'pending_fb_{i }.db')
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ('DELETE FROM pending_feedback')
        conn .commit ()
        conn .close ()

    for index ,feedback in enumerate (pending_feedbacks ):
        db_number =(index %NUM_DATABASES )+1 
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

def get_all_existing_vouch_numbers ():
    """
    Returns a set of all vouch_numbers found in various feedback-related databases.
    """
    directories =[
    PENDING_FEEDBACK_DIR ,
    "verificationdatabase",
    "rejectedfeedbacks",
    "premiumpendingfeedback",
    "premiumverificationfeedback"
    ]
    existing_numbers =set ()
    for directory in directories :
        if not os .path .exists (directory ):
            continue 
        for file in os .listdir (directory ):
            if file .endswith (".db"):
                db_path =os .path .join (directory ,file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT name FROM sqlite_master WHERE type='table';")
                    tables =cursor .fetchall ()
                    for table_tuple in tables :
                        table_name =table_tuple [0 ]
                        cursor .execute (f"PRAGMA table_info({table_name });")
                        columns =cursor .fetchall ()
                        column_names =[col [1 ]for col in columns ]
                        if "vouch_number"in column_names :
                            try :
                                cursor .execute (f"SELECT vouch_number FROM {table_name };")
                                rows =cursor .fetchall ()
                                for row in rows :
                                    existing_numbers .add (row [0 ])
                            except Exception :
                                continue 
                    conn .close ()
                except Exception :
                    continue 
    return existing_numbers 

def generate_vouch_number ():
    """
    Generates a unique 16-digit feedback ID.
    """
    existing_numbers =get_all_existing_vouch_numbers ()
    while True :
        vouch_number =''.join (random .choices (string .digits ,k =16 ))
        if vouch_number not in existing_numbers :
            return vouch_number 
