
import os 
import sqlite3 


DATABASE_DIR ="colordatabase"

def create_database_file (file_path ):
    """Creates a new SQLite database file with the colors table."""
    try :
        conn =sqlite3 .connect (file_path )
        c =conn .cursor ()
        c .execute ('''
            CREATE TABLE IF NOT EXISTS colors (
                user_id TEXT PRIMARY KEY,
                color TEXT,
                colorlock TEXT
            )
        ''')
        conn .commit ()
    except sqlite3 .Error as e :
        print (f"Error creating database file {file_path }: {e }")
    finally :
        conn .close ()

def get_db_files (database_dir =DATABASE_DIR ):
    """
    Returns a sorted list of database file paths from the database directory.
    Only files following the naming format "color_#.db" are returned.
    """
    files =[]
    if not os .path .exists (database_dir ):
        os .makedirs (database_dir )
    for filename in os .listdir (database_dir ):
        if filename .startswith ("color_")and filename .endswith (".db"):
            try :
                num =int (filename [6 :-3 ])
                files .append ((num ,filename ))
            except ValueError :
                continue 
    files .sort (key =lambda x :x [0 ])
    return [os .path .join (database_dir ,filename )for _ ,filename in files ]

def find_user_db (user_id ,database_dir =DATABASE_DIR ):
    """
    Searches all database files for the user’s record.
    Returns the file path if the user is found; otherwise returns None.
    """
    db_files =get_db_files (database_dir )
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            c =conn .cursor ()

            c .execute ('''
                CREATE TABLE IF NOT EXISTS colors (
                    user_id TEXT PRIMARY KEY,
                    color TEXT,
                    colorlock TEXT
                )
            ''')
            conn .commit ()
            c .execute ("SELECT * FROM colors WHERE user_id=?",(user_id ,))
            result =c .fetchone ()
        except sqlite3 .Error as e :
            print (f"Error accessing database {db_file }: {e }")
            result =None 
        finally :
            conn .close ()
        if result :
            return db_file 
    return None 

def get_active_db (database_dir =DATABASE_DIR ):
    """
    Returns the current (active) database file for inserting new entries.
    If the latest database already has 20,000 entries, a new database is created.
    """
    db_files =get_db_files (database_dir )
    if not db_files :
        file_path =os .path .join (database_dir ,"color_1.db")
        create_database_file (file_path )
        return file_path 

    active_db =db_files [-1 ]
    try :
        conn =sqlite3 .connect (active_db )
        c =conn .cursor ()

        c .execute ('''
            CREATE TABLE IF NOT EXISTS colors (
                user_id TEXT PRIMARY KEY,
                color TEXT,
                colorlock TEXT
            )
        ''')
        conn .commit ()
        c .execute ("SELECT COUNT(*) FROM colors")
        count =c .fetchone ()[0 ]
    except sqlite3 .Error as e :
        print (f"Error checking active database {active_db }: {e }")
        count =0 
    finally :
        conn .close ()

    if count >=20000 :
        base =os .path .basename (active_db )
        current_index =int (base [6 :-3 ])
        new_index =current_index +1 
        new_db =os .path .join (database_dir ,f"color_{new_index }.db")
        create_database_file (new_db )
        return new_db 
    else :
        return active_db 
