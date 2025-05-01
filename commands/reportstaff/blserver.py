import discord 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
import os 
import logging 




from config import REPORT_STAFF_ROLE ,SERVER_BLACKLIST_CHANNEL_ID 


logging .basicConfig (level =logging .INFO )
logger =logging .getLogger (__name__ )

IST =pytz .timezone ("Asia/Kolkata")

class BlacklistServer (commands .Cog ):
    MAX_ENTRIES_PER_DB =5000 
    DB_PREFIX ="server_"
    DB_EXTENSION =".db"
    DB_DIRECTORY ="serverblacklistdatabase"

    def __init__ (self ,bot ):
        self .bot =bot 


        os .makedirs (self .DB_DIRECTORY ,exist_ok =True )


        self .current_db_number ,self .conn ,self .cursor =self ._initialize_database ()

    def _initialize_database (self ):
        """
        Initializes the database by finding the latest database file and checking its entry count.
        If the latest database has reached the maximum number of entries, a new database is created.
        """
        try :
            db_files =[
            f for f in os .listdir (self .DB_DIRECTORY )
            if f .startswith (self .DB_PREFIX )and f .endswith (self .DB_EXTENSION )
            ]

            if not db_files :

                db_number =1 
                db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{db_number }{self .DB_EXTENSION }")
                conn ,cursor =self ._create_database (db_path )
                logger .info (f"Created new database: {db_path }")
                return db_number ,conn ,cursor 
            else :

                db_numbers =[]
                for f in db_files :
                    try :
                        number =int (f [len (self .DB_PREFIX ):-len (self .DB_EXTENSION )])
                        db_numbers .append (number )
                    except ValueError :
                        continue 

                if not db_numbers :

                    db_number =1 
                    db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{db_number }{self .DB_EXTENSION }")
                    conn ,cursor =self ._create_database (db_path )
                    logger .info (f"Created new database: {db_path }")
                    return db_number ,conn ,cursor 

                db_number =max (db_numbers )
                db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{db_number }{self .DB_EXTENSION }")
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()


                cursor .execute ("SELECT COUNT(*) FROM server_blacklist")
                count =cursor .fetchone ()[0 ]

                if count >=self .MAX_ENTRIES_PER_DB :

                    db_number +=1 
                    db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{db_number }{self .DB_EXTENSION }")
                    conn ,cursor =self ._create_database (db_path )
                    logger .info (f"Created new database: {db_path }")
                else :
                    logger .info (f"Using existing database: {db_path } with {count } entries")

                return db_number ,conn ,cursor 
        except Exception as e :
            logger .error (f"Error initializing database: {e }")
            raise e 

    def _create_database (self ,db_path ):
        """
        Creates a new SQLite database and the required table.
        """
        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ('''
                CREATE TABLE IF NOT EXISTS server_blacklist (
                    server_id TEXT PRIMARY KEY,
                    blacklisted_by_username TEXT,
                    blacklisted_by_id TEXT,
                    reason TEXT,
                    timestamp TEXT
                )
            ''')
            conn .commit ()
            return conn ,cursor 
        except sqlite3 .Error as e :
            logger .error (f"SQLite error while creating database {db_path }: {e }")
            raise e 

    def _get_current_database (self ):
        """
        Retrieves the current database connection. If the current database is full,
        it creates a new one.
        """
        try :
            self .cursor .execute ("SELECT COUNT(*) FROM server_blacklist")
            count =self .cursor .fetchone ()[0 ]
            if count >=self .MAX_ENTRIES_PER_DB :

                self .conn .close ()
                self .current_db_number +=1 
                db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{self .current_db_number }{self .DB_EXTENSION }")
                self .conn ,self .cursor =self ._create_database (db_path )
                logger .info (f"Created new database: {db_path }")
            return self .conn ,self .cursor 
        except sqlite3 .Error as e :
            logger .error (f"SQLite error while accessing current database: {e }")
            raise e 

    @commands .command (
    name ="blserver",
    usage ="+blserver <server_id> <reason>",
    help ="Blacklists a server by ID with a specified reason."
    )
    @commands .check (lambda ctx :any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ))
    async def blserver (self ,ctx ,server_id :str ,*,reason :str ):
        """Blacklists a server by ID and records the user/time/reason in the database."""
        try :

            if not server_id .isdigit ():
                await ctx .send ("**Invalid Server ID.** Please provide a numeric server ID.")
                return 

            server =self .bot .get_guild (int (server_id ))if server_id .isdigit ()else None 

            blacklisted_by_username =str (ctx .author )
            blacklisted_by_id =str (ctx .author .id )

            timestamp_ist =datetime .now (IST )
            timestamp_ist_str =timestamp_ist .strftime ("%Y-%m-%d %H:%M:%S IST")


            conn ,cursor =self ._get_current_database ()


            cursor .execute ('''
                INSERT OR REPLACE INTO server_blacklist
                (server_id, blacklisted_by_username, blacklisted_by_id, reason, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''',(server_id ,blacklisted_by_username ,blacklisted_by_id ,reason ,timestamp_ist_str ))
            conn .commit ()


            cursor .execute ("SELECT COUNT(*) FROM server_blacklist")
            count =cursor .fetchone ()[0 ]
            if count >=self .MAX_ENTRIES_PER_DB :
                logger .info (f"Database server_{self .current_db_number }.db reached {count } entries.")


            webhook_embed =discord .Embed (
            title ="Server Blacklisted",
            color =discord .Color .red (),
            timestamp =timestamp_ist 
            )
            webhook_embed .add_field (name ="Server ID",value =server_id ,inline =False )
            webhook_embed .add_field (name ="Reason",value =reason ,inline =False )
            webhook_embed .add_field (
            name ="Blacklisted By",
            value =f"{blacklisted_by_username } (ID: {blacklisted_by_id })",
            inline =False 
            )

            webhook_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )


            if server and server .icon :
                webhook_embed .set_thumbnail (url =server .icon .url )


            webhook_embed .set_image (
            url ="https://media.discordapp.net/attachments/1200750312844165203/1333069504888049674/serverblacklisted.png?ex=67978d39&is=67963bb9&hm=1d0722f935058c0778beb082474fce9153b98b1c7e924e9db297fc145dac5a47&=&format=webp&quality=lossless"
            )


            try :
                channel =self .bot .get_channel (SERVER_BLACKLIST_CHANNEL_ID )
                if channel is None :
                    logger .error ("Server blacklist channel not found. Check SERVER_BLACKLIST_CHANNEL_ID.")
                    await ctx .send ("**Server blacklist channel not found.**")
                    return 
                await channel .send (embed =webhook_embed )
            except Exception as e :
                logger .error (f"Unexpected error while sending the message to the channel: {e }")
                await ctx .send ("**An unexpected error occurred while sending the blacklist message.**")
                return 



            confirmation_embed =discord .Embed (
            title ="**Server Blacklist Confirmation**",
            description =f"Server with ID `{server_id }` has been blacklisted successfully.",
            color =0x00FF00 ,
            timestamp =timestamp_ist 
            )
            confirmation_embed .add_field (name ="Reason",value =reason ,inline =False )
            confirmation_embed .add_field (name ="Blacklisted By",value =ctx .author .mention ,inline =False )
            confirmation_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )

            await ctx .send (embed =confirmation_embed )

        except commands .MissingRequiredArgument :
            error_embed =discord .Embed (
            title ="Missing Arguments",
            description ="Usage: `+blserver <server_id> <reason>`",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =error_embed )
        except commands .MissingRole :
            error_embed =discord .Embed (
            title ="Insufficient Permissions",
            description ="You do not have the required role to execute this command.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =error_embed )
        except sqlite3 .Error as db_err :
            logger .error (f"Database error: {db_err }")
            error_embed =discord .Embed (
            title ="Database Error",
            description ="A database error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =error_embed )
        except Exception as e :
            logger .error (f"Unexpected error in blserver command: {e }")
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =error_embed )

    @blserver .error 
    async def blserver_error (self ,ctx ,error ):
        """Handles errors for the blserver command."""
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="Missing Arguments",
            description ="Usage: `+blserver <server_id> <reason>`",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
        elif isinstance (error ,commands .MissingRole ):
            embed =discord .Embed (
            title ="Insufficient Permissions",
            description ="You do not have the required role to execute this command.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
        else :
            logger .error (f"Unhandled error in blserver command: {error }")
            embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (BlacklistServer (bot ))
