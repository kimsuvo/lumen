

import os 
import sqlite3 
from datetime import datetime ,timedelta 
from zoneinfo import ZoneInfo 
import requests 



REDEEM_DB_DIR ="redeemcodes"
PREMIUM_DB_DIR ="premiumdatabase"
IMAGEDB_DIR ="imagedatabase"
CREDENTIALS_DATABASE_DIR ="credentialsdatabase"
BADGES_DB_DIR ="badgesdatabase"

PREMIUM_TABLE ="premium"
REDEEM_TABLE ="codes"
MAX_USERS_PER_DB =10000 
MAX_IMAGEDB_ENTRIES =10000 
MAX_BADGESDB_ENTRIES =15000 


os .makedirs (REDEEM_DB_DIR ,exist_ok =True )
os .makedirs (PREMIUM_DB_DIR ,exist_ok =True )
os .makedirs (IMAGEDB_DIR ,exist_ok =True )
os .makedirs (CREDENTIALS_DATABASE_DIR ,exist_ok =True )
os .makedirs (BADGES_DB_DIR ,exist_ok =True )





def verify_gumroad_license (license_key :str ,product_id :str ="tZZcLnTKDi2TF5gduAFLzw==")->int |None :
    """
    Verify the license key with Gumroad's API.

    Example API response:
    {
      "success": true,
      "uses": 3,
      "purchase": {
         "seller_id": "kL0psVL2admJSYRNs-OCMg==",
         "product_id": "32-nPAicqbLj8B_WswVlMw==",
         "product_name": "licenses demo product",
         "permalink": "QMGY",
         "product_permalink": "https://sahil.gumroad.com/l/pencil",
         "email": "customer@example.com",
         "price": 0,
         "gumroad_fee": 0,
         "currency": "usd",
         "quantity": 1,
         "discover_fee_charged": false,
         "can_contact": true,
         "referrer": "direct",
         "card": { "visual": null, "type": null },
         "order_number": 524459935,
         "sale_id": "FO8TXN-dbxYaBdahG97Y-Q==",
         "sale_timestamp": "2021-01-05T19:38:56Z",
         "purchaser_id": "5550321502811",
         "subscription_id": "GDzW4_aBdQc-o7Gbjng7lw==",
         "variants": "",
         "license_key": "85DB562A-C11D4B06-A2335A6B-8C079166",
         "is_multiseat_license": false,
         "ip_country": "United States",
         "recurrence": "monthly",
         "is_gift_receiver_purchase": false,
         "refunded": false,
         "disputed": false,
         "dispute_won": false,
         "id": "FO8TXN-dvaYbBbahG97a-Q==",
         "created_at": "2021-01-05T19:38:56Z",
         "custom_fields": [],
         "chargebacked": false,
         "subscription_ended_at": null,
         "subscription_cancelled_at": null,
         "subscription_failed_at": null
      }
    }

    If the license is valid, this function returns a premium duration (in days) based on the recurrence:
      - "monthly" returns 30 days,
      - "quarterly" returns 90 days,
      - "yearly" returns 365 days,
      - If no recurrence is provided, it returns a default of 30 days.

    If the license is invalid or any error occurs, it returns None.
    """
    url ="https://api.gumroad.com/v2/licenses/verify"
    payload ={
    "product_id":product_id ,
    "license_key":license_key 
    }
    try :
        response =requests .post (url ,data =payload )
        data =response .json ()
        if data .get ("success")is True :
            purchase =data .get ("purchase")
            if purchase :
                recurrence =purchase .get ("recurrence")
                if recurrence :
                    rec =recurrence .lower ()
                    if rec =="monthly":
                        return 30 
                    elif rec =="quarterly":
                        return 90 
                    elif rec =="yearly":
                        return 365 
                    else :
                        return 30 
                else :

                    return 30 
        return None 
    except Exception as e :
        print (f"Error verifying license with Gumroad: {e }")
        return None 


def is_redeem_code_in_global (redeem_code :str )->bool :
    """
    Check the global premium database to see if the redeem code is already used.
    """
    premium_db_path =get_premium_db_path ()
    conn =sqlite3 .connect (premium_db_path )
    c =conn .cursor ()
    c .execute ("""
        CREATE TABLE IF NOT EXISTS premium (
            user_id TEXT PRIMARY KEY,
            redeem_code TEXT,
            duration INTEGER,
            start_date TEXT,
            expiry_date TEXT
        )
    """)
    conn .commit ()
    c .execute ("SELECT user_id FROM premium WHERE redeem_code = ?",(redeem_code ,))
    result =c .fetchone ()
    conn .close ()
    return result is not None 

def is_redeem_code_in_user_db (user_id :str ,redeem_code :str )->bool :
    """
    Check the user-specific premium database to see if the redeem code is already used.
    """
    premium_db_path =get_user_premium_db (user_id )
    conn =sqlite3 .connect (premium_db_path )
    c =conn .cursor ()
    c .execute ("""
        CREATE TABLE IF NOT EXISTS premium (
            user_id TEXT PRIMARY KEY,
            redeem_code TEXT,
            duration INTEGER,
            start_date TEXT,
            expiry_date TEXT
        )
    """)
    conn .commit ()
    c .execute ("SELECT user_id FROM premium WHERE redeem_code = ?",(redeem_code ,))
    result =c .fetchone ()
    conn .close ()
    return result is not None 


def get_premium_db_path ():
    """
    Finds a premium DB file in PREMIUM_DB_DIR that has less than MAX_USERS_PER_DB entries.
    If none exists, creates a new one with the next sequential number.
    Returns the file path of the chosen premium DB.
    """
    files =[f for f in os .listdir (PREMIUM_DB_DIR )
    if f .startswith ("premium_")and f .endswith (".db")]
    files .sort (key =lambda f :int (f .split ("_")[1 ].split (".")[0 ])
    if f .split ("_")[1 ].split (".")[0 ].isdigit ()else 0 )

    for filename in files :
        db_path =os .path .join (PREMIUM_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {PREMIUM_TABLE } (
                user_id TEXT PRIMARY KEY,
                redeem_code TEXT,
                duration INTEGER,
                start_date TEXT,
                expiry_date TEXT
            )
        """)
        conn .commit ()
        c .execute (f"SELECT COUNT(*) FROM {PREMIUM_TABLE }")
        count =c .fetchone ()[0 ]
        conn .close ()
        if count <MAX_USERS_PER_DB :
            return db_path 

    next_number =1 
    if files :
        last =files [-1 ]
        try :
            next_number =int (last .split ("_")[1 ].split (".")[0 ])+1 
        except ValueError :
            next_number =1 
    new_db_name =f"premium_{next_number }.db"
    new_db_path =os .path .join (PREMIUM_DB_DIR ,new_db_name )
    conn =sqlite3 .connect (new_db_path )
    c =conn .cursor ()
    c .execute (f"""
        CREATE TABLE IF NOT EXISTS {PREMIUM_TABLE } (
            user_id TEXT PRIMARY KEY,
            redeem_code TEXT,
            duration INTEGER,
            start_date TEXT,
            expiry_date TEXT
        )
    """)
    conn .commit ()
    conn .close ()
    return new_db_path 

def get_user_premium_db (user_id :str ):
    """
    Searches through all premium databases to locate the one containing the given user_id.
    Returns the path to that DB if found; otherwise, returns None.
    """
    for filename in os .listdir (PREMIUM_DB_DIR ):
        if not filename .startswith ("premium_")or not filename .endswith (".db"):
            continue 
        db_path =os .path .join (PREMIUM_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {PREMIUM_TABLE } (
                user_id TEXT PRIMARY KEY,
                redeem_code TEXT,
                duration INTEGER,
                start_date TEXT,
                expiry_date TEXT
            )
        """)
        conn .commit ()
        c .execute (f"SELECT 1 FROM {PREMIUM_TABLE } WHERE user_id = ?",(user_id ,))
        result =c .fetchone ()
        conn .close ()
        if result :
            return db_path 
    return None 

def user_has_premium (user_id :str )->bool :
    """
    Checks if the user already has premium by searching all premium databases.
    """
    return get_user_premium_db (user_id )is not None 

def find_and_consume_redeem_code (redeem_code :str ):
    """
    Searches for the given redeem code in all databases in the REDEEM_DB_DIR.
    If found, returns its duration and removes it from the DB.
    Returns None if the code was not found.
    """
    for filename in os .listdir (REDEEM_DB_DIR ):
        if not filename .endswith (".db"):
            continue 
        db_path =os .path .join (REDEEM_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {REDEEM_TABLE } (
                redeem_code TEXT PRIMARY KEY,
                duration INTEGER
            )
        """)
        conn .commit ()
        c .execute (f"SELECT duration FROM {REDEEM_TABLE } WHERE redeem_code = ?",(redeem_code ,))
        row =c .fetchone ()
        if row :
            duration =row [0 ]
            c .execute (f"DELETE FROM {REDEEM_TABLE } WHERE redeem_code = ?",(redeem_code ,))
            conn .commit ()
            conn .close ()
            return duration 
        conn .close ()
    return None 

def is_user_registered (user_id :str ):
    """
    Checks if the user is registered in any database in CREDENTIALS_DATABASE_DIR.
    """
    for db_file in os .listdir (CREDENTIALS_DATABASE_DIR ):
        if db_file .endswith (".db"):
            db_path =os .path .join (CREDENTIALS_DATABASE_DIR ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
    return False 



def get_badges_db_path ():
    """
    Finds a badges DB file in BADGES_DB_DIR that has less than MAX_BADGESDB_ENTRIES entries.
    If none exists, creates a new one with the next sequential number.
    Returns the file path of the chosen badges DB.
    """
    files =[f for f in os .listdir (BADGES_DB_DIR )
    if f .startswith ("badges_")and f .endswith (".db")]
    files .sort (key =lambda f :int (f .split ("_")[1 ].split (".")[0 ])
    if f .split ("_")[1 ].split (".")[0 ].isdigit ()else 0 )

    for filename in files :
        db_path =os .path .join (BADGES_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute ('''
            CREATE TABLE IF NOT EXISTS badges (
                user_id TEXT PRIMARY KEY,
                badge_count TEXT
            )
        ''')
        conn .commit ()
        c .execute ("SELECT COUNT(*) FROM badges")
        count =c .fetchone ()[0 ]
        conn .close ()
        if count <MAX_BADGESDB_ENTRIES :
            return db_path 

    next_number =1 
    if files :
        last =files [-1 ]
        try :
            next_number =int (last .split ("_")[1 ].split (".")[0 ])+1 
        except ValueError :
            next_number =1 
    new_db_name =f"badges_{next_number }.db"
    new_db_path =os .path .join (BADGES_DB_DIR ,new_db_name )
    conn =sqlite3 .connect (new_db_path )
    c =conn .cursor ()
    c .execute ('''
        CREATE TABLE IF NOT EXISTS badges (
            user_id TEXT PRIMARY KEY,
            badge_count TEXT
        )
    ''')
    conn .commit ()
    conn .close ()
    return new_db_path 

def get_image_db_path ():
    """
    Finds an image DB file in IMAGEDB_DIR that has less than MAX_IMAGEDB_ENTRIES entries.
    If none exists, creates a new one with the next sequential number.
    Returns the file path of the chosen image DB.
    """
    files =[f for f in os .listdir (IMAGEDB_DIR )
    if f .startswith ("image_")and f .endswith (".db")]
    files .sort (key =lambda f :int (f .split ("_")[1 ].split (".")[0 ])
    if f .split ("_")[1 ].split (".")[0 ].isdigit ()else 0 )

    for filename in files :
        db_path =os .path .join (IMAGEDB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute ('''
            CREATE TABLE IF NOT EXISTS imagethumbnail (
                user_id INTEGER PRIMARY KEY,
                thumbnail TEXT DEFAULT '',
                image TEXT DEFAULT '',
                DWC TEXT DEFAULT 'no'
            )
        ''')
        conn .commit ()
        c .execute ("SELECT COUNT(*) FROM imagethumbnail")
        count =c .fetchone ()[0 ]
        conn .close ()
        if count <MAX_IMAGEDB_ENTRIES :
            return db_path 

    next_number =1 
    if files :
        last =files [-1 ]
        try :
            next_number =int (last .split ("_")[1 ].split (".")[0 ])+1 
        except ValueError :
            next_number =1 
    new_db_name =f"image_{next_number }.db"
    new_db_path =os .path .join (IMAGEDB_DIR ,new_db_name )
    conn =sqlite3 .connect (new_db_path )
    c =conn .cursor ()
    c .execute ('''
        CREATE TABLE IF NOT EXISTS imagethumbnail (
            user_id INTEGER PRIMARY KEY,
            thumbnail TEXT DEFAULT '',
            image TEXT DEFAULT '',
            DWC TEXT DEFAULT 'no'
        )
    ''')
    conn .commit ()
    conn .close ()
    return new_db_path 

def update_or_insert_image (user_id :str ,thumbnail :str ,image :str ):
    """
    Checks if a user's image record exists in any image DB.
    If it does, updates it; if not, inserts it into a DB that has available capacity.
    """
    user_id_int =int (user_id )
    for filename in os .listdir (IMAGEDB_DIR ):
        if not filename .startswith ("image_")or not filename .endswith (".db"):
            continue 
        db_path =os .path .join (IMAGEDB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute ('''
            CREATE TABLE IF NOT EXISTS imagethumbnail (
                user_id INTEGER PRIMARY KEY,
                thumbnail TEXT DEFAULT '',
                image TEXT DEFAULT '',
                DWC TEXT DEFAULT 'no'
            )
        ''')
        conn .commit ()
        c .execute ("SELECT 1 FROM imagethumbnail WHERE user_id = ?",(user_id_int ,))
        if c .fetchone ():
            c .execute ('''
                UPDATE imagethumbnail
                SET thumbnail = ?, image = ?
                WHERE user_id = ?
            ''',(thumbnail ,image ,user_id_int ))
            conn .commit ()
            conn .close ()
            return 
        conn .close ()

    db_path =get_image_db_path ()
    conn =sqlite3 .connect (db_path )
    c =conn .cursor ()
    c .execute ('''
         CREATE TABLE IF NOT EXISTS imagethumbnail (
             user_id INTEGER PRIMARY KEY,
             thumbnail TEXT DEFAULT '',
             image TEXT DEFAULT '',
             DWC TEXT DEFAULT 'no'
         )
    ''')
    conn .commit ()
    c .execute ('''
         INSERT INTO imagethumbnail (user_id, thumbnail, image)
         VALUES (?, ?, ?)
         ON CONFLICT(user_id) DO UPDATE SET
             thumbnail = excluded.thumbnail,
             image = excluded.image
    ''',(user_id_int ,thumbnail ,image ))
    conn .commit ()
    conn .close ()

def update_badges (user_id :str ):
    """
    Inserts or updates the badges database for a user.
    If a record exists, it prefixes the premium badge to the existing badge_count.
    If not, it creates a new record.
    """
    premium_badge ="<:lumen_premium_badge:1335561446284857445>"
    for filename in os .listdir (BADGES_DB_DIR ):
        if not filename .startswith ("badges_")or not filename .endswith (".db"):
            continue 
        db_path =os .path .join (BADGES_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute ('''
            CREATE TABLE IF NOT EXISTS badges (
                user_id TEXT PRIMARY KEY,
                badge_count TEXT
            )
        ''')
        conn .commit ()
        c .execute ("SELECT badge_count FROM badges WHERE user_id = ?",(user_id ,))
        row =c .fetchone ()
        if row :
            current =row [0 ]if row [0 ]is not None else ""
            if not current .startswith (premium_badge ):
                new_badge =premium_badge +(" "+current if current .strip ()!=""else "")
                c .execute ("UPDATE badges SET badge_count = ? WHERE user_id = ?",(new_badge ,user_id ))
                conn .commit ()
            conn .close ()
            return 
        conn .close ()

    db_path =get_badges_db_path ()
    conn =sqlite3 .connect (db_path )
    c =conn .cursor ()
    c .execute ('''
        CREATE TABLE IF NOT EXISTS badges (
            user_id TEXT PRIMARY KEY,
            badge_count TEXT
        )
    ''')
    conn .commit ()
    c .execute ("INSERT INTO badges (user_id, badge_count) VALUES (?, ?)",(user_id ,premium_badge ))
    conn .commit ()
    conn .close ()
