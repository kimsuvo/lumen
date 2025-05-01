

import os 
import sqlite3 


IMAGE_DB_DIR ="imagedatabase"
IMAGE_DB_PREFIX ="image_"
MAX_USERS_PER_DB =10000 


os .makedirs (IMAGE_DB_DIR ,exist_ok =True )

def find_user_database (user_id :str )->str :
    """
    Search through the image databases to find the one that contains the given user_id.
    Returns the database path if found; otherwise, returns None.
    """
    db_index =1 
    while True :
        db_path =os .path .join (IMAGE_DB_DIR ,f"{IMAGE_DB_PREFIX }{db_index }.db")
        if os .path .exists (db_path ):
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM imagethumbnail WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return db_path 
        else :
            break 
        db_index +=1 
    return None 

def get_available_database ()->str :
    """
    Finds an existing database that is not full (less than MAX_USERS_PER_DB)
    or creates a new one if needed.
    """
    db_index =1 
    while True :
        db_path =os .path .join (IMAGE_DB_DIR ,f"{IMAGE_DB_PREFIX }{db_index }.db")
        if os .path .exists (db_path ):
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT COUNT(*) FROM imagethumbnail")
            user_count =cursor .fetchone ()[0 ]
            conn .close ()
            if user_count <MAX_USERS_PER_DB :
                return db_path 
        else :

            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ('''
                CREATE TABLE IF NOT EXISTS imagethumbnail (
                    user_id TEXT PRIMARY KEY,
                    thumbnail TEXT DEFAULT '',
                    image TEXT DEFAULT '',
                    DWC TEXT DEFAULT 'no'
                )
            ''')
            conn .commit ()
            conn .close ()
            return db_path 
        db_index +=1 

def ensure_user_exists (user_id :str ,key :str ,value :str )->None :
    """
    Ensures that the user exists in one of the image databases.
    If not, the user is inserted into an available database.
    """
    existing_db =find_user_database (user_id )
    db_path =existing_db if existing_db is not None else get_available_database ()

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ("SELECT COUNT(*) FROM imagethumbnail WHERE user_id = ?",(user_id ,))
    user_exists =cursor .fetchone ()[0 ]

    if user_exists ==0 :

        cursor .execute ('''
            INSERT INTO imagethumbnail (user_id, thumbnail, image, DWC)
            VALUES (?, ?, ?, 'no')
        ''',(user_id ,value if key =="thumbnail"else "",value if key =="image"else ""))
    conn .commit ()
    conn .close ()

def get_user_data (user_id :str )->dict :
    """
    Retrieves the user data (thumbnail, image, DWC) from the appropriate database.
    Returns a dictionary or None if the user is not found.
    """
    db_path =find_user_database (user_id )
    if not db_path :
        return None 

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ("SELECT user_id, thumbnail, image, DWC FROM imagethumbnail WHERE user_id = ?",(user_id ,))
    user_data =cursor .fetchone ()
    conn .close ()

    if user_data :
        return {
        "user_id":user_data [0 ],
        "thumbnail":user_data [1 ],
        "image":user_data [2 ],
        "DWC":user_data [3 ]
        }
    return None 

def update_image_data (user_id :str ,key :str ,value :str )->None :
    """
    Updates a given column (thumbnail or image) for the user.
    If the user does not exist, they are added.
    """
    db_path =find_user_database (user_id )
    if not db_path :

        ensure_user_exists (user_id ,key ,value )
        return 

    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute (f"UPDATE imagethumbnail SET {key } = ? WHERE user_id = ?",(value ,user_id ))
    conn .commit ()
    conn .close ()
