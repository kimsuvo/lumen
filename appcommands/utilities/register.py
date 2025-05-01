import discord 
from discord .ext import commands 
from discord import app_commands 
import bcrypt 
import sqlite3 
from datetime import datetime 
import pytz 
import re 
import os 
import random 
import string 



def user_exists_in_ban_db (user_id :int )->bool :
    """
    Checks if a user with the given user_id exists in any database inside the bandatabase directory.
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

def generate_unique_key (length =64 ):
    """
    Generates a unique key containing symbols, numbers, uppercase, and lowercase letters,
    excluding backticks (`).
    """
    characters =string .ascii_letters +string .digits +string .punctuation .replace ('`','')
    return ''.join (random .choices (characters ,k =length ))

def initialize_database (db_path ):
    """
    Initializes the database by creating the 'users' table.
    """
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        recovery_email TEXT,
        created_by TEXT,
        created_at TEXT,
        key TEXT UNIQUE NOT NULL
    )''')
    conn .commit ()
    conn .close ()

def get_current_db_path ():
    """
    Retrieves the current database path with available space.
    Creates a new one if all existing databases are full.
    """
    directory ="credentialsdatabase"
    if not os .path .exists (directory ):
        os .makedirs (directory )

    db_files =sorted (
    [f for f in os .listdir (directory )if re .match (r'^credentials(_\d+)?\.db$',f )],
    key =lambda x :int (x .split ('_')[1 ].split ('.')[0 ])if '_'in x else 1 
    )

    if not db_files :
        first_db_path =os .path .join (directory ,"credentials_1.db")
        initialize_database (first_db_path )
        return first_db_path 

    for db_file in db_files :
        db_path =os .path .join (directory ,db_file )
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            recovery_email TEXT,
            created_by TEXT,
            created_at TEXT,
            key TEXT UNIQUE NOT NULL
        )''')
        cursor .execute ("SELECT COUNT(*) FROM users")
        count =cursor .fetchone ()[0 ]
        conn .close ()
        if count <5000 :
            return db_path 

    new_db_number =len (db_files )+1 
    new_db_name =f"credentials_{new_db_number }.db"
    new_db_path =os .path .join (directory ,new_db_name )
    initialize_database (new_db_path )

    return new_db_path 

def user_exists_in_any_db (user_id :int )->bool :
    """
    Checks if a user with the given user_id exists in any database inside the credentialsdatabase directory.
    """
    directory ="credentialsdatabase"
    if not os .path .exists (directory ):
        return False 

    for filename in os .listdir (directory ):
        if re .match (r'^credentials(_\d+)?\.db$',filename ):
            db_path =os .path .join (directory ,filename )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            if cursor .fetchone ():
                conn .close ()
                return True 
            conn .close ()
    return False 



class ShowKeyButton (discord .ui .Button ):
    def __init__ (self ,profile_key :str ):
        super ().__init__ (label ="Show Lumen Profile Key",style =discord .ButtonStyle .secondary )
        self .profile_key =profile_key 

    async def callback (self ,interaction :discord .Interaction ):
        await interaction .response .send_message (f"{self .profile_key }",ephemeral =True )
        self .disabled =True 
        await interaction .message .edit (view =self .view )



class RegisterCog (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 
        if not os .path .exists ("credentialsdatabase"):
            os .makedirs ("credentialsdatabase")

    @app_commands .command (name ="register",description ="Register with Lumen using a username and password.")
    @app_commands .describe (username ="Your desired username",password ="Your desired password")
    async def register (self ,interaction :discord .Interaction ,username :str ,password :str ):
        target_user_id =interaction .user .id 


        if user_exists_in_ban_db (target_user_id ):
            await interaction .response .send_message ("You are banned from Lumen.",ephemeral =True )
            return 


        if " "in username or " "in password :
            await interaction .response .send_message ("Username and password must not contain any spaces.",ephemeral =True )
            return 


        pattern =re .compile (r'^[A-Za-z][A-Za-z0-9._]*$')
        if not pattern .fullmatch (username ):
            await interaction .response .send_message (
            "Invalid username. It must start with an English letter and can only contain English letters, numbers, underscores, or periods.",
            ephemeral =True ,
            )
            return 


        if user_exists_in_any_db (target_user_id ):
            await interaction .response .send_message ("You're already registered.",ephemeral =True )
            return 

        try :

            hashed_username =bcrypt .hashpw (username .encode (),bcrypt .gensalt ()).decode ()
            hashed_password =bcrypt .hashpw (password .encode (),bcrypt .gensalt ()).decode ()


            unique_key =generate_unique_key ()


            db_path =get_current_db_path ()
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()


            cursor .execute ('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    recovery_email TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    key TEXT UNIQUE NOT NULL
                )
            ''')


            cursor .execute ("SELECT * FROM users WHERE key = ?",(unique_key ,))
            while cursor .fetchone ():
                unique_key =generate_unique_key ()
                cursor .execute ("SELECT * FROM users WHERE key = ?",(unique_key ,))


            created_at =datetime .now (pytz .timezone ("Asia/Kolkata")).strftime ("%Y-%m-%d %H:%M:%S")
            cursor .execute (
            '''INSERT INTO users 
                   (user_id, username, password, created_by, created_at, key) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
            (
            target_user_id ,
            hashed_username ,
            hashed_password ,
            str (interaction .user ),
            created_at ,
            unique_key 
            )
            )
            conn .commit ()
            conn .close ()


            await interaction .response .send_message (
            f"User **{username }** registered successfully! Please check your DMs for your Lumen Profile Key.",
            ephemeral =True 
            )


            dm_embed =discord .Embed (
            title ="Thank you for registering with Lumen!",
            description =(
            f"Your username is **{username }**.\n\n"
            "Click the button below to reveal your **Lumen Profile Key**. The button will be disabled automatically after 24 hours for security.\n\n"
            "**Important Precautions**:\n"
            "- Your Profile Key is confidential. Do not share it with anyone.\n"
            "- The support team will never ask for your Profile Key.\n"
            "- Store your Profile Key securely. Losing it may result in difficulty accessing your account.\n"
            "- If you suspect any unauthorized access, reset your credentials and contact support.\n\n"
            "Thank you for joining Lumen!"
            ),
            color =0x000001 ,
            )
            dm_embed .set_footer (text =f"Notification sent at {created_at }")
            dm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?format=webp&quality=lossless&width=671&height=671")
            view =discord .ui .View (timeout =86400 )
            view .add_item (ShowKeyButton (profile_key =unique_key ))

            try :
                user =await interaction .client .fetch_user (target_user_id )
                await user .send (embed =dm_embed ,view =view )
            except discord .Forbidden :
                await interaction .followup .send (
                "Could not send your credentials via DM. Please ensure your DMs are open.",
                ephemeral =True ,
                )
        except Exception as e :
            if not interaction .response .is_done ():
                await interaction .response .send_message (f"An error occurred: {e }",ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (RegisterCog (bot ))
