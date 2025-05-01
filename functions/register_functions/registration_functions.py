

import os 
import re 
import sqlite3 
import random 
import string 
import bcrypt 
from datetime import datetime 
import pytz 
import discord 
from discord import ButtonStyle ,Embed 
from discord .ui import Modal ,TextInput ,Button ,View 



def generate_unique_key (length =64 ):
    """
    Generates a unique 64-character key excluding backticks.
    """
    characters =string .ascii_letters +string .digits +string .punctuation .replace ('`','')
    return ''.join (random .choices (characters ,k =length ))

def is_user_registered (user_id ):
    """
    Checks if the user exists in any credentials database.
    """
    directory ="credentialsdatabase"
    if not os .path .exists (directory ):
        return False 
    for db_file in os .listdir (directory ):
        if db_file .endswith (".db"):
            db_path =os .path .join (directory ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
    return False 

def get_current_db_path ():
    """
    Retrieves the current credentials database path.
    Creates a new one if needed.
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
            user_id TEXT PRIMARY KEY,
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

def initialize_database (db_path ):
    """
    Creates the users table in the given credentials database.
    """
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        recovery_email TEXT,
        created_by TEXT,
        created_at TEXT,
        key TEXT UNIQUE NOT NULL
    )''')
    conn .commit ()
    conn .close ()

def user_exists_in_any_db (user_id :int )->bool :
    """
    Checks if the user exists in any credentials database.
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



class RegisterModal (Modal ):
    def __init__ (self ):
        super ().__init__ (title ="Register with Lumen")

        self .username_input =TextInput (
        label ="Username",
        placeholder ="Enter your username",
        style =discord .TextStyle .short ,
        min_length =1 ,
        max_length =40 ,
        )
        self .password_input =TextInput (
        label ="Password",
        placeholder ="Enter a secure password",
        style =discord .TextStyle .short ,
        min_length =6 ,
        max_length =40 ,
        )

        self .add_item (self .username_input )
        self .add_item (self .password_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        target_user_id =interaction .user .id 




        plain_username =self .username_input .value .strip ()
        raw_password =self .password_input .value .strip ()
        pattern =re .compile (r'^[A-Za-z][A-Za-z0-9._]*$')

        if " "in plain_username or " "in raw_password :
            await interaction .response .send_message ("Username and password must not contain any spaces.",ephemeral =True )
            return 

        if not plain_username :
            await interaction .response .send_message ("Username cannot be empty.",ephemeral =True )
            return 

        if not pattern .fullmatch (plain_username ):
            await interaction .response .send_message (
            "Invalid username. It must start with an English letter and can only contain English letters, numbers, underscores, or periods.",
            ephemeral =True ,
            )
            return 

        if user_exists_in_any_db (target_user_id ):
            await interaction .response .send_message ("You're already registered.",ephemeral =True )
            return 


        hashed_username =bcrypt .hashpw (plain_username .encode (),bcrypt .gensalt ()).decode ()
        hashed_password =bcrypt .hashpw (raw_password .encode (),bcrypt .gensalt ()).decode ()

        unique_key =generate_unique_key ()
        db_path =get_current_db_path ()
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()

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

        await interaction .response .send_message (f"User {plain_username } registered successfully!",ephemeral =True )


        dm_embed =Embed (
        title ="**Thank you for registering with Lumen!**",
        description =(
        f"Your username is **{plain_username }**.\n\n"
        "Click the button below to reveal your **Lumen Profile Key**.\n"
        "The button will be disabled automatically after 24 hours for security.\n\n"
        "**Important Precautions:**\n"
        "- Do not share your profile key with anyone.\n"
        "- The support team will never ask for your profile key.\n"
        "- Store your key securely.\n\n"
        "**Next Steps:**\n"
        "- Click the button below to view your Profile Key.\n"
        "- Copy and save it safely for future reference."
        ),
        color =0x000001 ,
        )
        dm_embed .set_footer (text =f"Notification sent at {created_at }")
        view =View (timeout =86400 )
        view .add_item (ShowKeyButton (profile_key =unique_key ))
        try :
            user_obj =await interaction .client .fetch_user (target_user_id )
            await user_obj .send (embed =dm_embed ,view =view )
        except discord .Forbidden :
            await interaction .followup .send ("Could not send your credentials via DM. Please ensure your DMs are open.",ephemeral =True )

class RegisterButton (Button ):
    def __init__ (self ,authorized_user :discord .User ):
        super ().__init__ (label ="REGISTER WITH LUMEN",style =ButtonStyle .success )
        self .authorized_user =authorized_user 

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .authorized_user :
            await interaction .response .send_message (
            "You cannot click this button as this command was initiated by another user.",
            ephemeral =True 
            )
            return 
        await interaction .response .send_modal (RegisterModal ())

class ShowKeyButton (Button ):
    def __init__ (self ,profile_key :str ):
        super ().__init__ (label ="Show Lumen Profile Key",style =ButtonStyle .secondary )
        self .profile_key =profile_key 

    async def callback (self ,interaction :discord .Interaction ):
        await interaction .response .send_message (f"{self .profile_key }",ephemeral =True )
        self .disabled =True 
        await interaction .message .edit (view =self .view )
