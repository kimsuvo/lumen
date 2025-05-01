import os 
import sqlite3 
from glob import glob 


PRODUCTS_DB_DIR ="productsdatabase"
CREDENTIALS_DB_DIR ="credentialsdatabase"
PREMIUM_DB_DIR ="premiumdatabase"


os .makedirs (PRODUCTS_DB_DIR ,exist_ok =True )
os .makedirs (CREDENTIALS_DB_DIR ,exist_ok =True )
os .makedirs (PREMIUM_DB_DIR ,exist_ok =True )

def get_product_db ():
    db_files =sorted (glob (os .path .join (PRODUCTS_DB_DIR ,"products_*.db")))
    if not db_files :
        new_db_path =os .path .join (PRODUCTS_DB_DIR ,"products_1.db")
        create_products_db (new_db_path )
        return new_db_path 

    last_db_path =db_files [-1 ]
    if count_users_in_db (last_db_path )>=5000 :
        new_db_number =int (last_db_path .split ("_")[-1 ].split (".")[0 ])+1 
        new_db_path =os .path .join (PRODUCTS_DB_DIR ,f"products_{new_db_number }.db")
        create_products_db (new_db_path )
        return new_db_path 

    return last_db_path 

def create_products_db (db_path ):
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ("""
        CREATE TABLE IF NOT EXISTS services_and_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            store TEXT,
            products TEXT
        )
    """)
    conn .commit ()
    conn .close ()

def count_users_in_db (db_path ):
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ("SELECT COUNT(*) FROM services_and_products")
    count =cursor .fetchone ()[0 ]
    conn .close ()
    return count 

def find_user_db (user_id ):
    db_files =sorted (glob (os .path .join (PRODUCTS_DB_DIR ,"products_*.db")))
    for db_file in db_files :
        conn =sqlite3 .connect (db_file )
        cursor =conn .cursor ()
        cursor .execute ("SELECT 1 FROM services_and_products WHERE user_id = ?",(str (user_id ),))
        exists =cursor .fetchone ()
        conn .close ()
        if exists :
            return db_file 
    return None 

def get_services_and_products (user_id ):
    db_file =find_user_db (user_id )
    if not db_file :
        return "No set yet.",[]

    conn =sqlite3 .connect (db_file )
    cursor =conn .cursor ()
    cursor .execute ("""
        SELECT store, products FROM services_and_products
        WHERE user_id = ?
    """,(str (user_id ),))
    result =cursor .fetchone ()
    conn .close ()

    if result :
        store ,products =result 
        products_list =products .split ("\n")if products else []
        return store if store else "No set yet.",products_list 
    return "No set yet.",[]

def update_services_and_products (user_id ,key ,value ):
    db_file =find_user_db (user_id )
    if not db_file :
        db_file =get_product_db ()

    conn =sqlite3 .connect (db_file )
    cursor =conn .cursor ()
    cursor .execute ("SELECT * FROM services_and_products WHERE user_id = ?",(str (user_id ),))
    user_data =cursor .fetchone ()

    if not user_data :
        cursor .execute ("""
            INSERT INTO services_and_products (user_id, store, products)
            VALUES (?, ?, ?)
        """,(str (user_id ),"",""))


    if key =="products":
        from functions .premium_functions .premium_user_functions import is_user_premium 

        max_products =5 if is_user_premium (user_id )else 3 
        value ="\n".join ([f"- {product }"for product in value [:max_products ]])



    cursor .execute (f"""
        UPDATE services_and_products
        SET {key } = ?
        WHERE user_id = ?
    """,(value ,str (user_id )))

    conn .commit ()
    conn .close ()

def is_user_registered (user_id :int )->bool :
    db_files =sorted (glob (os .path .join (CREDENTIALS_DB_DIR ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 

def is_user_premium (user_id :int )->bool :
    db_files =sorted (glob (os .path .join (PREMIUM_DB_DIR ,"*.db")))
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
