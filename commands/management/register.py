import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 
from discord .ui import Button ,View ,Modal ,TextInput 
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


        if user_exists_in_ban_db (target_user_id ):
            await interaction .response .send_message ("You are banned from Lumen.",ephemeral =True )
            return 


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

        try :

            if user_exists_in_any_db (target_user_id ):
                await interaction .response .send_message ("You're already registered.",ephemeral =True )
                return 


            hashed_username =bcrypt .hashpw (plain_username .encode (),bcrypt .gensalt ()).decode ()
            hashed_password =bcrypt .hashpw (raw_password .encode (),bcrypt .gensalt ()).decode ()


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


            await interaction .response .send_message (f"User {plain_username } registered successfully!",ephemeral =True )


            dm_embed =discord .Embed (
            title ="**Thank you for registering with Lumen!**",
            description =(
            f"Your username is **{plain_username }**.\n\n"
            "Click the button below to reveal your **Lumen Profile Key**.\n"
            "The button below will get disabled automatically after 24 hours for security.\n\n"

            "**__Important Precautions__**:\n"
            "-# 1. Your Profile Key is **confidential**. Do **not** share it with anyone.\n"
            "-# 2. The support team will **never** ask for your Profile Key. If someone does, report it immediately.\n"
            "-# 3. Store your Profile Key securely. Losing it may result in difficulty accessing your account.\n"
            "-# 4. If you suspect any unauthorized access, reset your credentials and contact support.\n\n"

            "**__Next Steps__**:\n"
            "-# - Click the button below to view your Profile Key securely.\n"
            "-# - Make sure to **copy and store it safely** for future reference.\n"
            "-# - If you encounter any issues, reach out to our support team.\n\n"

            "**Thank you for joining Lumen!** We’re excited to have you on board."
            ),
            color =0x000001 ,

            )
            dm_embed .set_footer (text =f"Notification sent at {created_at }")
            dm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=679f46d4&is=679df554&hm=d06244e816b6313e972c32884707e28f56c7bb6db764b212f541130b5cdeb4e5&=&format=webp&quality=lossless&width=670&height=670")
            view =View (timeout =86400 )
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


class RegisterButton (Button ):
    def __init__ (self ,authorized_user :discord .User ):
        super ().__init__ (label ="REGISTER WITH LUMEN",style =discord .ButtonStyle .success )
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
        super ().__init__ (label ="Show Lumen Profile Key",style =discord .ButtonStyle .secondary )
        self .profile_key =profile_key 

    async def callback (self ,interaction :discord .Interaction ):
        await interaction .response .send_message (
        f"{self .profile_key }",ephemeral =True 
        )
        self .disabled =True 
        await interaction .message .edit (view =self .view )



class PreRegisterModal (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        if not os .path .exists ("credentialsdatabase"):
            os .makedirs ("credentialsdatabase")

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command (name ="register")
    async def register_panel (self ,ctx ):

        embed =discord .Embed (
        title ="**Create an Account at Lumen**",
        description =(
        "Welcome to the **Lumen Registration Panel**! Let's get you started with your account.\n\n"

        "**__How to Register__**:\n"
        "**Set a unique username** for your account:\n"
        "-# 1. It must start with an English letter.\n"
        "-# 2. It cannot contain spaces.\n"
        "-# 3. Only English letters, numbers, underscores (_), or periods (.) are allowed.\n"
        "-# 4. Avoid using offensive or inappropriate words in your username, as this may result in account suspension.\n"
        "**Choose a secure password** to protect your account:\n"
        "-# 1. Your password must be strong and unique.\n"
        "-# 2. Spaces are not allowed in the password.\n"
        "-# 3. Avoid using easily guessable passwords such as ‘password123’ or your username.\n"
        "-# 4. Consider using a mix of uppercase letters, lowercase letters, numbers, and special characters for enhanced security.\n\n"

        "**__Next Steps__**:\n"
        "-# 1. Click the button below to begin the registration process.\n"
        "-# 2. Follow the instructions carefully to complete your setup quickly and efficiently.\n"
        "-# 3. Make sure to review your details before submission, as incorrect information may cause issues during login.\n\n"

        "**__Important Information__**:\n"
        "-# 1. Ensure your **DMs are open** so the bot can send you your account details.\n"
        "-# 2. If your DMs are closed, please adjust your settings or contact support for assistance.\n"
        "-# 3. Do not share your account credentials with anyone. The support team will never ask for your password.\n"
        "-# 4. If you suspect any unauthorized activity, reset your password immediately and report it to support.\n"
        "-# 5. Any violation of our platform’s **terms of service** may lead to suspension or termination of your account.\n\n"

        "**Need help?** Feel free to reach out to our support team for guidance."
        ),
        color =0x000001 

        )
        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?format=webp&quality=lossless&width=671&height=671")


        button =RegisterButton (authorized_user =ctx .author )
        view =View ()
        view .add_item (button )


        await ctx .send (embed =embed ,view =view )

    @register_panel .error 
    async def register_panel_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):
            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =f"You're on cooldown! Please try again in **{error .retry_after :.1f} seconds**.",
            color =0xff0000 ,
            timestamp =discord .utils .utcnow ()
            )
            cooldown_embed .set_footer (
            text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :
            raise error 




async def setup (bot ):
    await bot .add_cog (PreRegisterModal (bot ))
