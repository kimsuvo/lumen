import sqlite3 
import os 
import random 


MAX_USERS_PER_DB =5000 

class DatabaseManager :
    def __init__ (self ,db_dir ,db_prefix ):
        """
        Initialize the manager with the directory and database filename prefix.
        """
        self .db_dir =db_dir 
        self .db_prefix =db_prefix 
        os .makedirs (self .db_dir ,exist_ok =True )

    def get_all_db_paths (self ):
        """
        Return a sorted list of database file paths in the directory.
        """
        return sorted ([
        os .path .join (self .db_dir ,db )
        for db in os .listdir (self .db_dir )
        if db .startswith (self .db_prefix )and db .endswith ('.db')
        ])

    def find_user_db (self ,user_id ):
        """
        Search through all databases for one that contains the given user_id.
        Returns the path if found, else None.
        """
        for db_path in self .get_all_db_paths ():
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT 1 FROM warnings WHERE user_id = ? LIMIT 1",(str (user_id ),))
            result =c .fetchone ()
            conn .close ()
            if result :
                return db_path 
        return None 

    def get_db_with_space (self ):
        """
        Look for a database file that has fewer than MAX_USERS_PER_DB unique users.
        Returns the database path if one is found, else None.
        """
        for db_path in self .get_all_db_paths ():
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT COUNT(DISTINCT user_id) FROM warnings")
            count =c .fetchone ()[0 ]
            conn .close ()
            if count <MAX_USERS_PER_DB :
                return db_path 
        return None 

    def create_new_db (self ):
        """
        Create a new database file with an incremented suffix and initialize the warnings table.
        Returns the path to the new database.
        """
        existing_dbs =self .get_all_db_paths ()
        next_index =1 
        if existing_dbs :
            last_db =existing_dbs [-1 ]
            basename =os .path .basename (last_db )
            try :
                last_index =int (basename .replace (self .db_prefix ,'').replace ('.db',''))
                next_index =last_index +1 
            except ValueError :
                pass 
        new_db_name =f"{self .db_prefix }{next_index }.db"
        new_db_path =os .path .join (self .db_dir ,new_db_name )
        conn =sqlite3 .connect (new_db_path )
        c =conn .cursor ()
        c .execute ('''CREATE TABLE IF NOT EXISTS warnings (
                        user_id TEXT,
                        warn_id TEXT,
                        reason TEXT
                    )''')
        conn .commit ()
        conn .close ()
        return new_db_path 

    def insert_warning (self ,db_path ,user_id ,warn_id ,reason ):
        """
        Insert a new warning into the specified database.
        """
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (
        "INSERT INTO warnings (user_id, warn_id, reason) VALUES (?, ?, ?)",
        (str (user_id ),warn_id ,reason )
        )
        conn .commit ()
        conn .close ()

    def warn_id_exists (self ,warn_id ):
        """
        Check if a warn_id already exists in any of the databases.
        """
        for db_path in self .get_all_db_paths ():
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT 1 FROM warnings WHERE warn_id = ? LIMIT 1",(warn_id ,))
            if c .fetchone ():
                conn .close ()
                return True 
            conn .close ()
        return False 

    def generate_unique_warn_id (self ):
        """
        Generate a random warn ID that does not exist in any database.
        """
        while True :
            warn_id =str (random .randint (1000000000 ,9999999999 ))
            if not self .warn_id_exists (warn_id ):
                return warn_id 

    def remove_warning (self ,warn_id ):
        """
        Remove a warning (by warn_id) from all databases.
        Returns True if at least one warning was found and removed, otherwise False.
        """
        found =False 
        for db_path in self .get_all_db_paths ():
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT * FROM warnings WHERE warn_id = ?",(warn_id ,))
            if c .fetchone ():
                c .execute ("DELETE FROM warnings WHERE warn_id = ?",(warn_id ,))
                conn .commit ()
                found =True 
            conn .close ()
        return found 

    def get_warnings_for_user (self ,user_id ):
        """
        Retrieve a list of warnings (warn_id and reason) for the specified user.
        """
        warnings =[]
        for db_path in self .get_all_db_paths ():
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT warn_id, reason FROM warnings WHERE user_id = ?",(str (user_id ),))
            warnings .extend (c .fetchall ())
            conn .close ()
        return warnings 
