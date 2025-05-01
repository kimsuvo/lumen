

import os 
import re 
import sqlite3 
import random 
import string 
from datetime import datetime 
import pytz 
import discord 
from dateutil .parser import parse as dateutil_parse 
from dateutil import tz 
from functions .premium_functions .premium_user_functions import is_user_premium 



def get_verified_tick (user_id :int )->str :
    db_dir ="verifiedusers"
    user_id_str =str (user_id )
    if not os .path .exists (db_dir ):
        return ""
    for filename in os .listdir (db_dir ):
        if re .match (r"verified_\d+\.db",filename ):
            db_path =os .path .join (db_dir ,filename )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()

            c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
            conn .commit ()
            c .execute ("SELECT tick_name FROM verified WHERE user_id = ?",(user_id_str ,))
            row =c .fetchone ()
            conn .close ()
            if row :
                return row [0 ]
    return ""


def get_custom_button (user_id ):
    """
    Checks all databases in the 'custombuttondatabase' directory for a custom button entry
    for the given user_id. Returns a tuple (button_name, url) if found; otherwise, returns None.
    """
    db_directory ="custombuttondatabase"
    if not os .path .exists (db_directory ):
        return None 
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT button_name, url FROM custombuttons WHERE user_id = ?",(str (user_id ),))
                result =cursor .fetchone ()
                conn .close ()
                if result :
                    return result 
            except sqlite3 .Error as e :
                print (f"Error checking custom button in {db_file }: {e }")
                continue 
    return None 

def normalize_store_url (store :str )->str :
    """
    Normalizes the store URL.
    """

    match =re .search (r'\((https?://[^\s)]+)\)',store )
    if match :
        return match .group (1 )
    if store .startswith ("discord.gg"):
        return "https://"+store 
    if "discord.gg"in store and not store .startswith ("http"):
        return "https://"+store 
    return store 

def get_store_button_status (user_id ):
    """
    Returns True if the store button is enabled for the user.
    """
    db_directory ="buttonsdatabase"
    if not os .path .exists (db_directory ):
        return False 
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT storebutton FROM buttons WHERE user_id = ?",(str (user_id ),))
                result =cursor .fetchone ()
                conn .close ()
                if result and result [0 ].strip ().lower ()=="yes":
                    return True 
            except sqlite3 .Error as e :
                print (f"Error fetching storebutton status from {db_file }: {e }")
                continue 
    return False 


def get_user_status (user_id ):
    """
    Fetches the user's status from 'statuses' tables across all .db files
    in the statusdatabase directory. Returns '-# No status set yet.' if not found.
    """
    status ="-# No status set yet."
    db_directory ="statusdatabase"

    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )

    try :
        for db_file in os .listdir (db_directory ):
            if db_file .endswith (".db"):
                db_path =os .path .join (db_directory ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute ('SELECT status FROM statuses WHERE user_id = ?',(user_id ,))
                    result =cursor .fetchone ()

                    conn .close ()

                    if result :
                        status =result [0 ]
                        break 
                except sqlite3 .Error as e :
                    print (f"Error fetching user status from {db_file }: {e }")
                    continue 
    except Exception as e :
        print (f"Error in get_user_status: {e }")

    return status if status else "-# No status set yet."



def user_exists_in_ban_db (user_id :int )->bool :
    """
    Checks if the user is banned by searching databases in the 'bandatabase' directory.
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

def load_credentials ():
    """
    Loads all credentials from every .db file in the credentialsdatabase directory.
    """
    credentials_list =[]
    db_directory ="credentialsdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ('SELECT * FROM users')
                credentials =cursor .fetchall ()
                conn .close ()
                for credential in credentials :
                    credentials_list .append ({
                    'user_id':credential [0 ],
                    'username':credential [1 ],
                    'password':credential [2 ],
                    'recovery_email':credential [3 ],
                    'created_by':credential [4 ],
                    'created_at':credential [5 ],
                    'key':credential [6 ]
                    })
            except sqlite3 .Error as e :
                print (f"Error loading credentials from {db_file }: {e }")
                continue 
    return credentials_list 

def init_db ():
    """
    Initializes the 'services_and_products' table inside each .db file
    found in the productsdatabase directory.
    """
    db_directory ="productsdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ('''
                CREATE TABLE IF NOT EXISTS services_and_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    store TEXT,
                    products TEXT
                )
                ''')
                conn .commit ()
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error initializing products DB {db_file }: {e }")
                continue 

def load_services_and_products ():
    """
    Loads services and products from every .db file in the productsdatabase directory.
    """
    services_and_products =[]
    db_directory ="productsdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT user_id, store, products FROM services_and_products")
                rows =cursor .fetchall ()
                conn .close ()
                for row in rows :
                    user_id ,store ,products =row 
                    services_and_products .append ({
                    "user_id":user_id ,
                    "store":store or "",
                    "products":products .split ("\n")if products else []
                    })
            except sqlite3 .Error as e :
                print (f"Error loading services and products from {db_file }: {e }")
                continue 
    return services_and_products 

def get_user_badges (user_id ):
    """
    Fetches the badge count for a given user_id from the badgesdatabase.
    """
    badge_count_total =None 
    db_directory ="badgesdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT badge_count FROM badges WHERE user_id = ?",(str (user_id ),))
                result =cursor .fetchone ()
                conn .close ()
                if result :
                    badge_count_total =result [0 ]
                    break 
            except sqlite3 .Error as e :
                print (f"Error fetching badges from {db_file }: {e }")
                continue 
    if badge_count_total is not None :
        return badge_count_total 
    return "-# No badges assigned."

def init_imagethumbnail_tables ():
    """
    Creates the imagethumbnail table in each .db file in the imagedatabase directory.
    """
    db_directory ="imagedatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
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
            except sqlite3 .Error as e :
                print (f"Error initializing image thumbnail table in {db_file }: {e }")
                continue 

def ensure_user_exists (user_id ,key ,value ):
    """
    Ensures a row exists for the user_id in the imagethumbnail table.
    """
    db_directory ="imagedatabase"
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ('SELECT COUNT(*) FROM imagethumbnail WHERE user_id = ?',(user_id ,))
                user_exists =cursor .fetchone ()[0 ]
                if user_exists ==0 :
                    if key =="thumbnail":
                        cursor .execute ('''
                            INSERT INTO imagethumbnail (user_id, thumbnail, image, DWC)
                            VALUES (?, ?, ?, ?)
                        ''',(user_id ,value ,'','no'))
                    elif key =="image":
                        cursor .execute ('''
                            INSERT INTO imagethumbnail (user_id, thumbnail, image, DWC)
                            VALUES (?, ?, ?, ?)
                        ''',(user_id ,'',value ,'no'))
                    conn .commit ()
                    conn .close ()
                    return 
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error ensuring user exists in {db_file }: {e }")
                continue 

def update_image_data (user_id ,key ,value ):
    """
    Updates the given key (thumbnail or image) for the specified user_id.
    """
    db_directory ="imagedatabase"
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                ensure_user_exists (user_id ,key ,value )
                cursor .execute (f'''
                    INSERT INTO imagethumbnail (user_id, {key }, DWC)
                    VALUES (?, ?, 'no') 
                    ON CONFLICT(user_id) 
                    DO UPDATE SET {key } = excluded.{key };
                ''',(user_id ,value ))
                conn .commit ()
                conn .close ()
                return 
            except sqlite3 .Error as e :
                print (f"Error updating image data in {db_file }: {e }")
                continue 

def get_user_data (user_id ):
    """
    Retrieves image data (thumbnail, image, DWC) for a given user_id.
    """
    db_directory ="imagedatabase"
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                ensure_user_exists (user_id ,"thumbnail","")
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
            except sqlite3 .Error as e :
                print (f"Error fetching user data from {db_file }: {e }")
                continue 
    return None 

def get_feedback_counts (user_id ):
    """
    Fetches total, positive, and negative feedback counts and calculates global rank.
    """
    user_id_str =str (user_id )
    total_feedback_count =0 
    positive_feedback_count =0 
    negative_feedback_count =0 
    all_users_feedback =[]
    db_directory ="feedbackcountdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("""
                    SELECT total_feedback_count, positive_feedback_count, negative_feedback_count
                    FROM feedback_count 
                    WHERE receiver_id=?
                """,(user_id_str ,))
                result =cursor .fetchone ()
                if result :
                    total_feedback_count ,positive_feedback_count ,negative_feedback_count =result 
                cursor .execute ("SELECT receiver_id, positive_feedback_count FROM feedback_count")
                all_feedback =cursor .fetchall ()
                all_users_feedback .extend (all_feedback )
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error fetching feedback counts from {db_file }: {e }")
                continue 
    if positive_feedback_count is not None :
        sorted_feedbacks =sorted (all_users_feedback ,key =lambda x :x [1 ],reverse =True )
        global_rank =next ((index +1 for index ,(uid ,_ )in enumerate (sorted_feedbacks )if uid ==user_id_str ),0 )
        return positive_feedback_count ,negative_feedback_count ,total_feedback_count ,global_rank 
    return 0 ,0 ,0 ,0 


india_tz =tz .gettz ("Asia/Kolkata")

def parse_and_normalize (timestamp_str ):
    """
    Parses a timestamp string and normalizes it to an offset-aware datetime in IST.
    """
    dt =dateutil_parse (timestamp_str )
    if dt .tzinfo is None :
        dt =dt .replace (tzinfo =india_tz )
    return dt 

def get_latest_feedbacks (user_id ,limit =15 ):
    """
    Retrieves the latest 'limit' feedback entries for a given user_id.
    """
    feedbacks =[]
    table_name =f"feedback_{user_id }"
    db_directory ="feedbackdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute (
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name ,)
                )
                if cursor .fetchone ():
                    cursor .execute (f"SELECT giver_id, feedback, timestamp FROM {table_name }")
                    rows =cursor .fetchall ()
                    try :
                        sorted_rows =sorted (rows ,key =lambda row :parse_and_normalize (row [2 ]),reverse =True )
                    except Exception as e :
                        print (f"Error parsing timestamps: {e }")
                        sorted_rows =rows 
                    feedbacks =sorted_rows [:limit ]
                    conn .close ()
                    break 
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error fetching latest feedbacks from {db_file }: {e }")
                continue 
    return feedbacks 

def get_registration_date (user_id ):
    """
    Returns the registration date for the user in a Discord timestamp format.
    """
    credentials =load_credentials ()
    user_data =next ((u for u in credentials if str (u ['user_id'])==str (user_id )),None )
    if user_data :
        created_at =user_data .get ("created_at",None )
        if created_at :
            created_at =created_at .strip ()
            formats_to_try =[
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            ]
            for fmt in formats_to_try :
                try :
                    registration_date =datetime .strptime (created_at ,fmt )
                    registration_timestamp =int (registration_date .timestamp ())
                    return f"<t:{registration_timestamp }:F>"
                except ValueError :
                    continue 
            try :
                registration_date =dateutil_parse (created_at )
                registration_timestamp =int (registration_date .timestamp ())
                return f"<t:{registration_timestamp }:F>"
            except Exception :
                return "Invalid registration date format."
    return "[Click the button below to register](https://discord.gg/lumenbot)"

def get_services_and_products (user_id ):
    """
    Fetches the user's store and products.
    """
    store ="No store set"
    products_list =[]
    db_directory ="productsdatabase"
    for db_file in os .listdir (db_directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (db_directory ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT store, products FROM services_and_products WHERE user_id = ?",(str (user_id ),))
                result =cursor .fetchone ()
                conn .close ()
                if result :
                    store_result ,products =result 
                    if store_result :
                        store =store_result 
                    if products :
                        products_list .extend (products .split ("\n"))
            except sqlite3 .Error as e :
                print (f"Error fetching services and products from {db_file }: {e }")
                continue 

    products_list =list (dict .fromkeys (products_list ))


    max_products =5 if is_user_premium (user_id )else 3 


    products_list =products_list [:max_products ]

    if not products_list :
        products_list =["-# No products registered."]
    return store ,products_list 


def get_image_data (user_id ):
    """
    Fetches the user's thumbnail and image.
    """
    user_data =get_user_data (user_id )
    default_thumbnail ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png"
    default_image ="https://media.discordapp.net/attachments/1200750312844165203/1323958955025895454/lumen_banner.png"
    thumbnail =user_data ["thumbnail"]if user_data and user_data .get ("thumbnail")else default_thumbnail 
    image =user_data ["image"]if user_data and user_data .get ("image")else default_image 
    return thumbnail ,image 

def get_user_color (user_id ):
    """
    Returns the color for the user by searching the 'colordatabase'.
    """
    db_dir ="colordatabase"
    for filename in os .listdir (db_dir ):
        if filename .endswith (".db"):
            db_path =os .path .join (db_dir ,filename )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT color FROM colors WHERE user_id = ?",(str (user_id ),))
            result =c .fetchone ()
            conn .close ()
            if result and result [0 ]:
                color_str =result [0 ].strip ()
                if color_str .startswith ("#"):
                    color_str =color_str [1 :]
                try :
                    return int (color_str ,16 )
                except ValueError :
                    continue 
    return 0x000001 
