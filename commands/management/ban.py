import os 
import glob 
import sqlite3 
import datetime 
import discord 
from discord .ext import commands 
from discord import Embed ,ui 
from config import DEV_CHAMBER_ROLE ,BANNED_CHANNEL_ID 


DEFAULT_EMBED_COLOR =0xFF0000 
DEFAULT_EMBED_IMAGE_URL =(
"https://media.discordapp.net/attachments/1200750312844165203/1327173446773506068/"
"banned.png?ex=6782c2d7&is=67817157&hm=e72b342583e925603d53590e5e92de47f2bff596b6922142b72210063b56a27f"
"&=&format=webp&quality=lossless"
)


DATABASE_DIRS ={
"credentials":"credentialsdatabase",
"feedback":"feedbackdatabase",
"feedbackcount":"feedbackcountdatabase",
"products":"productsdatabase",
"images":"imagedatabase",
"colors":"colordatabase",
"premium":"premiumdatabase",
"badges":"badgesdatabase",
"status":"statusdatabase",
"info":"infodatabase",
"blacklists":"blacklistsdatabase",
"banned":"bandatabase",
}


for key ,directory in DATABASE_DIRS .items ():
    os .makedirs (directory ,exist_ok =True )



class BanConfirmationModal (ui .Modal ,title ="Confirm Ban"):
    confirm_input =ui .TextInput (
    label ="Type CONFIRM to proceed",
    placeholder ="CONFIRM",
    required =True ,
    max_length =10 
    )
    reason_input =ui .TextInput (
    label ="Reason for ban",
    placeholder ="Enter the reason for banning the user",
    style =discord .TextStyle .paragraph ,
    required =True ,
    max_length =200 
    )

    def __init__ (self ,author :discord .Member ,user :discord .User ,callback_fn ):
        """
        :param author: The member who initiated the ban command.
        :param user: The target user to ban.
        :param callback_fn: A function to call after successful modal submission.
        """
        super ().__init__ ()
        self .author =author 
        self .target_user =user 
        self .callback_fn =callback_fn 

    async def on_submit (self ,interaction :discord .Interaction ):

        if interaction .user .id !=self .author .id :
            await interaction .response .send_message ("You are not allowed to use this modal.",ephemeral =True )
            return 


        if self .confirm_input .value .strip ().upper ()!="CONFIRM":
            await interaction .response .send_message ("Confirmation text incorrect. Ban cancelled.",ephemeral =True )
            return 


        reason =self .reason_input .value .strip ()
        await interaction .response .send_message ("Ban confirmed. Processing...",ephemeral =True )
        await self .callback_fn (self .target_user ,reason )



class BanConfirmationView (ui .View ):
    def __init__ (self ,author :discord .Member ,target_user :discord .User ,callback_fn ):
        """
        :param author: The member who initiated the ban command.
        :param target_user: The target user to ban.
        :param callback_fn: Function to call after confirmation modal is submitted.
        """
        super ().__init__ (timeout =60 )
        self .author =author 
        self .target_user =target_user 
        self .callback_fn =callback_fn 

    async def interaction_check (self ,interaction :discord .Interaction )->bool :

        if interaction .user .id !=self .author .id :
            await interaction .response .send_message ("You cannot use these buttons.",ephemeral =True )
            return False 
        return True 

    @ui .button (label ="CONFIRM BAN",style =discord .ButtonStyle .danger )
    async def confirm_button (self ,interaction :discord .Interaction ,button :ui .Button ):

        modal =BanConfirmationModal (author =self .author ,user =self .target_user ,callback_fn =self .callback_fn )

        await interaction .response .send_modal (modal )


        for child in self .children :
            child .disabled =True 
        try :

            await interaction .message .edit (view =self )
        except Exception as e :
            print (f"Error editing message to disable buttons: {e }")

    @ui .button (label ="CANCEL BAN",style =discord .ButtonStyle .secondary )
    async def cancel_button (self ,interaction :discord .Interaction ,button :ui .Button ):

        for child in self .children :
            child .disabled =True 

        await interaction .response .edit_message (view =self )

        await interaction .followup .send ("Ban has been cancelled.",ephemeral =True )





class BanUser (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    def create_db_tables (self ):
        """
        Creates all necessary database tables in their respective directories.
        (This function may be called once on cog load if needed.)
        """
        try :

            conn =sqlite3 .connect (os .path .join (DATABASE_DIRS ["credentials"],"credentials.db"))
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

        except sqlite3 .Error as e :
            print (f"Error creating database tables: {e }")

    async def process_ban (self ,target_user :discord .User ,reason :str ):
        """
        This function will perform the full ban processing:
          - Insert the banned user into the appropriate banned_X.db (creating new ones as needed).
          - Delete or update the user's data from all relevant database directories.
          - Send a confirmation embed to the banned channel.
        (The detailed deletion/insertion logic is implemented in Part 2.)
        """

        pass 

    @commands .command ()
    @commands .has_role (DEV_CHAMBER_ROLE )
    async def ban (self ,ctx ,user :discord .User ):
        """
        Initiates the ban process for a user. A confirmation embed with buttons will be sent,
        and only the command invoker can confirm or cancel.
        """

        confirm_embed =Embed (
        title ="Confirm Ban",
        description =f"Are you sure you want to ban {user .mention }?",
        color =DEFAULT_EMBED_COLOR 
        )
        confirm_embed .set_thumbnail (url =user .display_avatar .url )


        view =BanConfirmationView (author =ctx .author ,target_user =user ,callback_fn =self .process_ban )
        await ctx .send (embed =confirm_embed ,view =view )



    async def process_ban (self ,target_user :discord .User ,reason :str ):
        """
        Processes the ban by:
         - Inserting the banned user into the appropriate banned_X.db file in bandatabase.
         - Deleting or updating user data from all relevant database directories.
         - Sending a confirmation embed to the banned channel.
        """
        user_id_str =str (target_user .id )
        current_time =datetime .datetime .utcnow ().strftime ("%Y-%m-%d %H:%M:%S")


        self .insert_into_banned_db (target_user ,reason ,current_time )


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["credentials"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM users WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["feedback"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                table_name =f"feedback_{target_user .id }"
                cursor .execute (f"DROP TABLE IF EXISTS {table_name }")
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["feedbackcount"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM feedback_count WHERE receiver_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["products"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM services_and_products WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 



        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["images"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ('''
                    INSERT OR REPLACE INTO imagethumbnail (user_id, thumbnail, image, DWC)
                    VALUES (?, ?, ?, ?)
                ''',(
                user_id_str ,
                "https://media.discordapp.net/attachments/1200750312844165203/1324664665548259419/"
                "blacklist_logo.png?ex=6778f99b&is=6777a81b&hm=40d4fb0255a8b3501be615f75bae09da2cfaf9489f9b43faa0343919166cc118"
                "&=&format=webp&quality=lossless&width=671&height=671",
                DEFAULT_EMBED_IMAGE_URL ,
                "yes"
                ))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["colors"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM colordata WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["premium"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()

                cursor .execute ("DELETE FROM premium WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["badges"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM badges WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["status"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM statuses WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["info"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()

                cursor .execute ("DELETE FROM info WHERE user_id = ?",(user_id_str ,))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        for db_file in glob .glob (os .path .join (DATABASE_DIRS ["blacklists"],"*.db")):
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()

                cursor .execute ('''
                    CREATE TABLE IF NOT EXISTS blacklists (
                        user_id TEXT PRIMARY KEY,
                        banned INTEGER,
                        banned_at TEXT
                    )
                ''')
                cursor .execute ('''
                    INSERT OR REPLACE INTO blacklists (user_id, banned, banned_at)
                    VALUES (?, ?, ?)
                ''',(user_id_str ,1 ,current_time ))
                conn .commit ()
                conn .close ()
            except sqlite3 .Error :
                continue 


        banned_channel =self .bot .get_channel (BANNED_CHANNEL_ID )
        if banned_channel :
            ban_embed =Embed (
            title ="User Banned",
            description =f"User {target_user .mention } has been banned.",
            color =DEFAULT_EMBED_COLOR ,
            timestamp =datetime .datetime .utcnow ()
            )
            ban_embed .set_thumbnail (url =target_user .display_avatar .url )
            ban_embed .add_field (name ="User ID",value =user_id_str ,inline =False )
            ban_embed .add_field (name ="Ban Reason",value =reason ,inline =False )
            ban_embed .add_field (name ="Banned At (UTC)",value =current_time ,inline =False )
            try :
                await banned_channel .send (embed =ban_embed )
            except Exception :
                pass 
        else :
            print (f"Could not find channel with ID: {BANNED_CHANNEL_ID }")

    def insert_into_banned_db (self ,target_user :discord .User ,reason :str ,banned_at :str ):
        """
        Inserts the banned user into a banned_X.db file in the bandatabase directory.
        Each banned_X.db holds up to 10,000 banned users; if the current file is full,
        a new database is created with an incremented number.
        """
        user_id_str =str (target_user .id )

        banned_files =glob .glob (os .path .join (DATABASE_DIRS ["banned"],"banned_*.db"))
        banned_files .sort (key =lambda x :int (os .path .splitext (os .path .basename (x ))[0 ].split ("_")[1 ]))

        target_db =None 
        if banned_files :

            latest_db =banned_files [-1 ]
            try :
                conn =sqlite3 .connect (latest_db )
                cursor =conn .cursor ()

                cursor .execute ('''
                    CREATE TABLE IF NOT EXISTS banned (
                        user_id TEXT PRIMARY KEY,
                        banned_at TEXT,
                        reason TEXT
                    )
                ''')
                conn .commit ()

                cursor .execute ("SELECT COUNT(*) FROM banned")
                count =cursor .fetchone ()[0 ]
                conn .close ()
                if count <10000 :
                    target_db =latest_db 
                else :
                    target_db =None 
            except sqlite3 .Error :
                target_db =None 

        if not target_db :

            if banned_files :
                last_number =int (os .path .splitext (os .path .basename (banned_files [-1 ]))[0 ].split ("_")[1 ])
                new_number =last_number +1 
            else :
                new_number =1 
            target_db =os .path .join (DATABASE_DIRS ["banned"],f"banned_{new_number }.db")
            try :
                conn =sqlite3 .connect (target_db )
                cursor =conn .cursor ()
                cursor .execute ('''
                    CREATE TABLE IF NOT EXISTS banned (
                        user_id TEXT PRIMARY KEY,
                        banned_at TEXT,
                        reason TEXT
                    )
                ''')
                conn .commit ()
                conn .close ()
            except sqlite3 .Error as e :
                print (f"Error creating banned database: {e }")
                return 


        try :
            conn =sqlite3 .connect (target_db )
            cursor =conn .cursor ()
            cursor .execute ('''
                INSERT OR REPLACE INTO banned (user_id, banned_at, reason)
                VALUES (?, ?, ?)
            ''',(user_id_str ,banned_at ,reason ))
            conn .commit ()
            conn .close ()
        except sqlite3 .Error as e :
            print (f"Error inserting into banned database: {e }")




async def setup (bot ):
    cog =BanUser (bot )


    await bot .add_cog (cog )
