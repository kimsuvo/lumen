

import sqlite3 
from datetime import datetime ,timedelta 
import glob 
from .constants import FEEDBACK_DATABASE_DIR 

def fetch_feedback_data (user_id :int ,days_int :str ):
    """
    Query all feedback databases to retrieve rows for the given user and timeframe.
    If days_int == "all", fetch all records. Otherwise, fetch from the last N days.
    Returns a list of rows or None if no databases are found.
    """
    all_rows =[]
    db_files =glob .glob (f"{FEEDBACK_DATABASE_DIR }/*.db")


    if not db_files :
        return None 

    table_name =f"feedback_{user_id }"
    for db_file in db_files :
        conn =sqlite3 .connect (db_file )
        cursor =conn .cursor ()
        cursor .execute ("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table_name ,))
        table_exists =cursor .fetchone ()

        if table_exists :
            if days_int =="all":
                query =f"SELECT * FROM {table_name }"
                cursor .execute (query )
            else :
                query =f"SELECT * FROM {table_name } WHERE timestamp >= ?"
                since_date =(datetime .now ()-timedelta (days =days_int )).strftime ('%Y-%m-%d %H:%M:%S')
                cursor .execute (query ,(since_date ,))
            rows =cursor .fetchall ()
            all_rows .extend (rows )
        conn .close ()

    return all_rows 
