import sqlite3 
import os 


DB_DIR ='imagedatabase'
if not os .path .exists (DB_DIR ):
    os .makedirs (DB_DIR )

DB_PREFIX ="image_"
MAX_USERS_PER_DB =10000 


def get_db_list ():
    """Fetch the list of existing database files in the directory."""
    return sorted ([f for f in os .listdir (DB_DIR )if f .startswith (DB_PREFIX )and f .endswith (".db")])


def get_db_path (db_number ):
    """Generate the path for a given database number."""
    return os .path .join (DB_DIR ,f"{DB_PREFIX }{db_number }.db")


def get_current_db ():
    """Finds the database that has space for new users or creates a new one."""
    db_files =get_db_list ()


    if not db_files :
        return get_db_path (1 )


    for db_file in db_files :
        db_path =os .path .join (DB_DIR ,db_file )
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()


        try :
            cursor .execute ("SELECT COUNT(*) FROM imagethumbnail")
            user_count =cursor .fetchone ()[0 ]
        except sqlite3 .OperationalError :
            user_count =0 
        conn .close ()

        if user_count <MAX_USERS_PER_DB :
            return db_path 


    new_db_number =len (db_files )+1 
    return get_db_path (new_db_number )


def create_imagethumbnail_table (db_path ):
    """Creates the imagethumbnail table in the given database."""
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()

    cursor .execute ('''
    CREATE TABLE IF NOT EXISTS imagethumbnail (
        user_id TEXT PRIMARY KEY,
        thumbnail TEXT,
        image TEXT,
        DWC TEXT
    )
    ''')

    conn .commit ()
    conn .close ()


def get_user_db (user_id ):
    """Finds which database contains the given user_id."""
    db_files =get_db_list ()

    for db_file in db_files :
        db_path =os .path .join (DB_DIR ,db_file )
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()

        cursor .execute ("SELECT * FROM imagethumbnail WHERE user_id = ?",(str (user_id ),))
        result =cursor .fetchone ()
        conn .close ()

        if result :
            return db_path 

    return None 


def get_user_data (user_id ):
    """Fetches user data from the correct database."""
    db_path =get_user_db (user_id )
    if not db_path :
        return None 

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()

    cursor .execute ("SELECT * FROM imagethumbnail WHERE user_id = ?",(str (user_id ),))
    result =cursor .fetchone ()
    conn .close ()

    if result :
        return {
        "user_id":result [0 ],
        "thumbnail":result [1 ],
        "image":result [2 ],
        "DWC":result [3 ]
        }
    return None 


def save_user_data (user_data ):
    """Adds a new user entry to the appropriate database."""
    existing_db =get_user_db (user_data ['user_id'])

    if existing_db :
        db_path =existing_db 
    else :
        db_path =get_current_db ()


    create_imagethumbnail_table (db_path )

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()

    cursor .execute ('''
    INSERT OR REPLACE INTO imagethumbnail (user_id, thumbnail, image, DWC)
    VALUES (?, ?, ?, ?)
    ''',(user_data ['user_id'],user_data ['thumbnail'],user_data ['image'],user_data ['DWC']))

    conn .commit ()
    conn .close ()


def update_image_data (user_id ,column ,value ):
    """Updates a specific column in the correct database."""
    db_path =get_user_db (user_id )

    if not db_path :
        return 

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()

    cursor .execute (f'''
    UPDATE imagethumbnail SET {column } = ? WHERE user_id = ?
    ''',(value ,str (user_id )))

    conn .commit ()
    conn .close ()


def is_user_dwc (user_id ):
    """Checks if a user is marked as DWC."""
    user_data =get_user_data (user_id )
    if user_data and user_data .get ("DWC","").lower ()=="yes":
        return True 
    return False 
