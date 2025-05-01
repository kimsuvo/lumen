import sqlite3 
import os 
from glob import glob 
import datetime 


STATUS_DB_DIR ="statusdatabase"
USERS_PER_DB =5000 

def ensure_status_db_dir ():
    os .makedirs (STATUS_DB_DIR ,exist_ok =True )

def create_status_table (db_path ,include_last_updated =True ):
    """
    Creates the 'statuses' table if it does not exist.
    If include_last_updated is True, the table will include a last_updated column.
    """
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    if include_last_updated :
        cursor .execute ("""CREATE TABLE IF NOT EXISTS statuses (
                            user_id INTEGER PRIMARY KEY,
                            status TEXT,
                            status_update_block TEXT,
                            last_updated TEXT DEFAULT (datetime('now'))
                          )""")
    else :
        cursor .execute ("""CREATE TABLE IF NOT EXISTS statuses (
                            user_id INTEGER PRIMARY KEY,
                            status TEXT,
                            status_update_block TEXT
                          )""")
    conn .commit ()
    conn .close ()

def find_user_db (user_id ):
    """
    Scans the STATUS_DB_DIR and returns the path of the database file
    that contains the given user's record.
    Returns None if not found.
    """
    ensure_status_db_dir ()
    for db_file in sorted (os .listdir (STATUS_DB_DIR )):
        if db_file .startswith ("status_")and db_file .endswith (".db"):
            db_path =os .path .join (STATUS_DB_DIR ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM statuses WHERE user_id = ?",(user_id ,))
            if cursor .fetchone ():
                conn .close ()
                return db_path 
            conn .close ()
    return None 

def get_db_for_insert (user_id ):
    """
    Finds an existing database that either already contains the user’s record or has space
    (fewer than USERS_PER_DB users). If no database exists, creates a new one.
    """
    ensure_status_db_dir ()
    db_index =1 
    while True :
        db_path =os .path .join (STATUS_DB_DIR ,f"status_{db_index }.db")

        if not os .path .exists (db_path ):
            create_status_table (db_path ,include_last_updated =True )
            return db_path 

        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        create_status_table (db_path ,include_last_updated =True )

        cursor .execute ("SELECT 1 FROM statuses WHERE user_id = ?",(user_id ,))
        if cursor .fetchone ():
            conn .close ()
            return db_path 


        cursor .execute ("SELECT COUNT(*) FROM statuses")
        count =cursor .fetchone ()[0 ]
        conn .close ()
        if count <USERS_PER_DB :
            return db_path 
        db_index +=1 

def update_user_status (user_id ,status ,status_update_block ='no',include_last_updated =True ):
    """
    Inserts or replaces a user’s status.
    When include_last_updated is True, updates the last_updated column to the current time.
    """

    db_path =find_user_db (user_id )or get_db_for_insert (user_id )

    create_status_table (db_path ,include_last_updated =include_last_updated )
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    if include_last_updated :
        cursor .execute ('''INSERT OR REPLACE INTO statuses 
                          (user_id, status, status_update_block, last_updated)
                          VALUES (?, ?, ?, datetime('now'))''',(user_id ,status ,status_update_block ))
    else :
        cursor .execute ('''INSERT OR REPLACE INTO statuses 
                          (user_id, status, status_update_block)
                          VALUES (?, ?, ?)''',(user_id ,status ,status_update_block ))
    conn .commit ()
    conn .close ()

def get_user_status (user_id ,include_last_updated =True ):
    """
    Retrieves a user’s status.
    Returns (status, status_update_block, last_updated) if include_last_updated is True,
    or (status, status_update_block) if False.
    If the user is not found, returns default values.
    """
    db_path =find_user_db (user_id )
    if not db_path :
        if include_last_updated :
            return (None ,'no',None )
        return (None ,'no')
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    if include_last_updated :
        cursor .execute ("SELECT status, status_update_block, last_updated FROM statuses WHERE user_id = ?",(user_id ,))
    else :
        cursor .execute ("SELECT status, status_update_block FROM statuses WHERE user_id = ?",(user_id ,))
    result =cursor .fetchone ()
    conn .close ()
    if result :
        return result 
    if include_last_updated :
        return (None ,'no',None )
    return (None ,'no')

def remove_user_status (user_id ):
    """
    Removes a user’s status record.
    """
    db_path =find_user_db (user_id )
    if db_path :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("DELETE FROM statuses WHERE user_id = ?",(user_id ,))
        conn .commit ()
        conn .close ()
