
import os 
import re 
import sqlite3 
import random 
from datetime import datetime 
import pytz 


PENDING_FEEDBACK_DB_DIR =os .path .join ("pendingfeedbackdatabase")
os .makedirs (PENDING_FEEDBACK_DB_DIR ,exist_ok =True )
PENDING_FEEDBACK_DB_FILES =[
os .path .join (PENDING_FEEDBACK_DB_DIR ,f"pending_fb_{i }.db")
for i in range (1 ,11 )
]

def create_feedback_db ():
    """Ensure that each pending feedback database has the required table."""
    for db_path in PENDING_FEEDBACK_DB_FILES :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ('''
            CREATE TABLE IF NOT EXISTS pending_feedback (
                vouch_number TEXT PRIMARY KEY,
                giver_id TEXT,
                receiver_id TEXT,
                feedback TEXT,
                timestamp TEXT,
                type TEXT
            )
        ''')
        conn .commit ()
        conn .close ()

def load_pending_feedback ():
    """Load all pending feedback entries from every pending feedback database."""
    feedback_list =[]
    for db_path in PENDING_FEEDBACK_DB_FILES :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT * FROM pending_feedback")
        rows =cursor .fetchall ()
        conn .close ()
        for row in rows :
            feedback ={
            "vouch_number":row [0 ],
            "giver_id":row [1 ],
            "receiver_id":row [2 ],
            "feedback":row [3 ],
            "timestamp":row [4 ],
            "type":row [5 ]
            }
            feedback_list .append (feedback )
    return feedback_list 

def get_all_existing_vouch_numbers ():
    """
    Retrieves all existing vouch numbers from multiple directories/databases.
    """
    directories =[
    PENDING_FEEDBACK_DB_DIR ,
    "verificationdatabase",
    "rejectedfeedbacks",
    os .path .join ("premiumpendingfeedback"),
    "premiumverificationfeedback"
    ]
    all_vouch_numbers =set ()
    for directory in directories :
        if os .path .exists (directory ):
            for db_file in os .listdir (directory ):
                if db_file .endswith (".db"):
                    db_path =os .path .join (directory ,db_file )
                    try :
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()
                        for table_name in ["pending_feedback","rejected_feedback"]:
                            cursor .execute (f"SELECT vouch_number FROM {table_name }")
                            rows =cursor .fetchall ()
                            for row in rows :
                                all_vouch_numbers .add (row [0 ])
                        conn .close ()
                    except Exception :
                        continue 
    return all_vouch_numbers 

def generate_vouch_number (extra_existing_vouch_numbers =set ()):
    """
    Generate a unique vouch number (a 16-digit integer) that is not present in any database.
    """
    all_vouch_numbers =get_all_existing_vouch_numbers ()|set (extra_existing_vouch_numbers )
    while True :
        vouch_number =random .randint (1000000000000000 ,9999999999999999 )
        if vouch_number not in all_vouch_numbers :
            return vouch_number 
