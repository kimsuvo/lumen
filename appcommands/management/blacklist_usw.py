import discord 
from discord import app_commands 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
import os 
import logging 
import requests 
from zoneinfo import ZoneInfo 
import config 
from functions .blacklist .db_utils import get_blacklist_db ,get_image_db 


logging .basicConfig (level =logging .INFO )
logger =logging .getLogger (__name__ )


IST =pytz .timezone ("Asia/Kolkata")


def is_staff (interaction :discord .Interaction )->bool :
    """Check if the invoking member has one of the required staff roles."""
    if not isinstance (interaction .user ,discord .Member ):
        return False 
    return any (role .id in config .REPORT_STAFF_ROLE for role in interaction .user .roles )



DATABASE_DIR ="blacklisted_wallet_crypto"
DATABASE_PREFIX ="crypto_wallet_"
DATABASE_LIMIT =20000 

def get_database_path ()->str :
    """Return a database path that has less than DATABASE_LIMIT entries,
    or a new database if all current ones are full."""
    if not os .path .exists (DATABASE_DIR ):
        os .makedirs (DATABASE_DIR ,exist_ok =True )
    db_index =1 
    while True :
        db_path =os .path .join (DATABASE_DIR ,f"{DATABASE_PREFIX }{db_index }.db")
        if not os .path .exists (db_path ):
            return db_path 
        else :
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute (
                "CREATE TABLE IF NOT EXISTS wallets (crypto_name TEXT, wallet_address TEXT, timestamp TEXT)"
                )
                conn .commit ()
                cursor .execute ("SELECT COUNT(*) FROM wallets")
                count =cursor .fetchone ()[0 ]
                conn .close ()
            except sqlite3 .Error as e :
                raise Exception ("Error accessing database: "+str (e ))
            if count <DATABASE_LIMIT :
                return db_path 
            else :
                db_index +=1 

def insert_wallet (crypto_name :str ,wallet_address :str )->tuple [str ,str ]:
    """Insert the wallet info into the appropriate database and return the timestamp and db used."""
    try :
        db_path =get_database_path ()
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute (
        "CREATE TABLE IF NOT EXISTS wallets (crypto_name TEXT, wallet_address TEXT, timestamp TEXT)"
        )
        timestamp =datetime .now (IST ).strftime ("%Y-%m-%d %H:%M:%S")
        cursor .execute (
        "INSERT INTO wallets (crypto_name, wallet_address, timestamp) VALUES (?, ?, ?)",
        (crypto_name ,wallet_address ,timestamp )
        )
        conn .commit ()
        conn .close ()
        return timestamp ,db_path 
    except sqlite3 .Error as e :
        raise Exception ("Database insertion error: "+str (e ))
    except Exception as e :
        raise Exception ("Unexpected error during database operation: "+str (e ))


@app_commands .guild_only ()
class BlacklistGroup (commands .GroupCog ,name ="blacklist"):
    """Cog for managing blacklists."""

    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 


        self .DB_DIRECTORY ="serverblacklistdatabase"
        self .DB_PREFIX ="server_"
        self .DB_EXTENSION =".db"
        self .MAX_ENTRIES_PER_DB =5000 
        os .makedirs (self .DB_DIRECTORY ,exist_ok =True )
        self .current_db_number ,self .server_conn ,self .server_cursor =self ._initialize_database ()


        self .blacklist_db_dir ="blacklistsdatabase"
        self .image_db_dir ="imagedatabase"
        os .makedirs (self .blacklist_db_dir ,exist_ok =True )
        os .makedirs (self .image_db_dir ,exist_ok =True )


        self .wallet_db_dir =DATABASE_DIR 
        if not os .path .exists (self .wallet_db_dir ):
            os .makedirs (self .wallet_db_dir ,exist_ok =True )

    def _initialize_database (self )->tuple [int ,sqlite3 .Connection ,sqlite3 .Cursor ]:
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
                cursor .execute ("CREATE TABLE IF NOT EXISTS server_blacklist (server_id TEXT PRIMARY KEY, blacklisted_by_username TEXT, blacklisted_by_id TEXT, reason TEXT, timestamp TEXT)")
                conn .commit ()
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

    def _create_database (self ,db_path :str )->tuple [sqlite3 .Connection ,sqlite3 .Cursor ]:
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

    def _get_current_database (self )->tuple [sqlite3 .Connection ,sqlite3 .Cursor ]:
        try :
            self .server_cursor .execute ("SELECT COUNT(*) FROM server_blacklist")
            count =self .server_cursor .fetchone ()[0 ]
            if count >=self .MAX_ENTRIES_PER_DB :
                self .server_conn .close ()
                self .current_db_number +=1 
                db_path =os .path .join (self .DB_DIRECTORY ,f"{self .DB_PREFIX }{self .current_db_number }{self .DB_EXTENSION }")
                self .server_conn ,self .server_cursor =self ._create_database (db_path )
                logger .info (f"Created new database: {db_path }")
            return self .server_conn ,self .server_cursor 
        except sqlite3 .Error as e :
            logger .error (f"SQLite error while accessing current database: {e }")
            raise e 


    @app_commands .command (
    name ="server",
    description ="Blacklist a server by ID with a specified reason."
    )
    @app_commands .check (is_staff )
    async def blacklist_server (self ,interaction :discord .Interaction ,server_id :str ,reason :str ):
        await interaction .response .defer (ephemeral =True )
        if not server_id .isdigit ():
            await interaction .followup .send ("**Invalid Server ID.** Please provide a numeric server ID.",ephemeral =True )
            return 

        server =self .bot .get_guild (int (server_id ))if server_id .isdigit ()else None 
        blacklisted_by_username =str (interaction .user )
        blacklisted_by_id =str (interaction .user .id )
        timestamp_ist =datetime .now (IST )
        timestamp_ist_str =timestamp_ist .strftime ("%Y-%m-%d %H:%M:%S IST")

        try :
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
                logger .info (f"Database {self .DB_PREFIX }{self .current_db_number }{self .DB_EXTENSION } reached {count } entries.")

            log_embed =discord .Embed (
            title ="Server Blacklisted",
            color =discord .Color .red (),
            timestamp =timestamp_ist 
            )
            log_embed .add_field (name ="Server ID",value =server_id ,inline =False )
            log_embed .add_field (name ="Reason",value =reason ,inline =False )
            log_embed .add_field (name ="Blacklisted By",value =f"{blacklisted_by_username } (ID: {blacklisted_by_id })",inline =False )
            log_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )
            if server and server .icon :
                log_embed .set_thumbnail (url =server .icon .url )
            log_embed .set_image (url ="https://media.discordapp.net/attachments/1200750312844165203/1333069504888049674/serverblacklisted.png?ex=67978d39&is=67963bb9&hm=1d0722f935058c0778beb082474fce9153b98b1c7e924e9db297fc145dac5a47&=&format=webp&quality=lossless")

            log_channel =self .bot .get_channel (config .SERVER_BLACKLIST_CHANNEL_ID )
            if log_channel is None :
                await interaction .followup .send ("**Server blacklist channel not found.**",ephemeral =True )
                return 

            await log_channel .send (embed =log_embed )

            confirmation_embed =discord .Embed (
            title ="**Server Blacklist Confirmation**",
            description =f"Server with ID `{server_id }` has been blacklisted successfully.",
            color =0x00FF00 ,
            timestamp =timestamp_ist 
            )
            confirmation_embed .add_field (name ="Reason",value =reason ,inline =False )
            confirmation_embed .add_field (name ="Blacklisted By",value =interaction .user .mention ,inline =False )
            confirmation_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )

            await interaction .followup .send (embed =confirmation_embed ,ephemeral =True )

        except sqlite3 .Error as db_err :
            logger .error (f"Database error: {db_err }")
            error_embed =discord .Embed (
            title ="Database Error",
            description ="A database error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )
        except Exception as e :
            logger .error (f"Unexpected error in blacklist_server command: {e }")
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )

    @blacklist_server .error 
    async def blacklist_server_error (self ,interaction :discord .Interaction ,error :Exception ):
        if isinstance (error ,app_commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="Missing Arguments",
            description ="Usage: `/blacklist server <server_id> <reason>`",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
        elif isinstance (error ,app_commands .MissingPermissions ):
            embed =discord .Embed (
            title ="Insufficient Permissions",
            description ="You do not have the required role to execute this command.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
        else :
            logger .error (f"Unhandled error in blacklist_server command: {error }")
            embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )



    @app_commands .command (
    name ="user",
    description ="Blacklist a user with a specified reason."
    )
    @app_commands .check (is_staff )
    async def blacklist_user (self ,interaction :discord .Interaction ,user :discord .User ,reason :str ):
        await interaction .response .defer ()
        user_id =str (user .id )
        processing_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Blacklisting User...**",
        color =0x000001 
        )
        processing_message =await interaction .followup .send (embed =processing_embed ,wait =True )

        try :

            conn ,cursor =get_blacklist_db (user_id ,db_dir =self .blacklist_db_dir )


            cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(user_id ,))
            if cursor .fetchone ():
                final_embed =discord .Embed (
                title ="**Blacklist Failed**",
                description =f"User {user .mention } is already blacklisted.",
                color =0x000001 
                )
                await processing_message .edit (embed =final_embed )
                conn .close ()
                return 


            cursor .execute ("INSERT INTO blacklists (user_id, blacklist_status) VALUES (?, ?)",(user_id ,'yes'))
            conn .commit ()
            conn .close ()


            img_conn ,img_cursor =get_image_db (user_id ,db_dir =self .image_db_dir )
            img_cursor .execute ("SELECT * FROM imagethumbnail WHERE user_id = ?",(user_id ,))
            if img_cursor .fetchone ():
                img_cursor .execute (
                "UPDATE imagethumbnail SET image = ?, thumbnail = ?, DWC = ? WHERE user_id = ?",
                (
                'https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless',
                'https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?format=webp&quality=lossless&width=671&height=671',
                'yes',
                user_id 
                )
                )
            else :
                img_cursor .execute (
                "INSERT INTO imagethumbnail (user_id, image, thumbnail, DWC) VALUES (?, ?, ?, ?)",
                (
                user_id ,
                'https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless',
                'https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?format=webp&quality=lossless&width=671&height=671',
                'yes'
                )
                )
            img_conn .commit ()
            img_conn .close ()


            requests .get (
            f"https://api.dezinare.com/users/add/blacklist/{user_id }",
            params ={"api_key":"TYqp12dvDYuvjF4ekI8Yd2EJIVXtRkV0"}
            )

            kolkata_tz =pytz .timezone ('Asia/Kolkata')
            timestamp =datetime .now (kolkata_tz ).strftime ("%Y-%m-%d %H:%M:%S IST")

            log_embed =discord .Embed (title ="**User Blacklisted**",color =discord .Color .from_str ("#ff0000"))
            if user .avatar :
                log_embed .set_thumbnail (url =user .avatar .url )
            log_embed .set_image (url ="https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless")
            log_embed .add_field (name ="Blacklisted By",value =interaction .user .mention ,inline =False )
            log_embed .add_field (name ="Blacklisted User",value =f"{user .mention } ({user .display_name })",inline =False )
            log_embed .add_field (name ="Blacklisted User ID",value =user_id ,inline =False )
            log_embed .add_field (name ="Username",value =user .name ,inline =False )
            log_embed .add_field (name ="Reason",value =reason ,inline =False )
            log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )

            blacklist_channel =self .bot .get_channel (config .BLACKLIST_CHANNEL_ID )
            if blacklist_channel :
                await blacklist_channel .send (embed =log_embed )
            else :
                await interaction .followup .send (
                "Error: Blacklist channel not found. Please check the channel ID.",
                ephemeral =True 
                )

            try :
                dm_embed =discord .Embed (
                title ="You Have Been Blacklisted from using our feedback system.",
                color =discord .Color .from_str ("#ff0000")
                )
                dm_embed .set_thumbnail (
                url ="https://media.discordapp.net/attachments/1200750312844165203/1327163059751358465/blacklist_logo.png?format=webp&quality=lossless"
                )
                dm_embed .add_field (name ="Blacklisted By",value =interaction .user .mention ,inline =False )
                dm_embed .add_field (name ="Reason",value =reason ,inline =False )
                dm_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
                await user .send (embed =dm_embed )
            except discord .Forbidden :
                dm_fail_embed =discord .Embed (
                title ="DM Failed",
                description =f"Could not DM {user .mention }. They might have DMs disabled.",
                color =discord .Color .from_str ("#ffcc00")
                )
                await interaction .followup .send (embed =dm_fail_embed ,ephemeral =True )

            success_embed =discord .Embed (
            title ="<:lumen_online:1324983167538696303> **Blacklist Successful**",
            description =f"User {user .mention } has been blacklisted.\n**Reason:** {reason }",
            color =0x000001 
            )
            await processing_message .edit (embed =success_embed )

        except sqlite3 .DatabaseError as e :
            error_embed =discord .Embed (
            title ="Database Error",
            description =f"There was an error interacting with the database: {str (e )}. Please try again later.",
            color =discord .Color .from_str ("#ff0000")
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )

    @blacklist_user .error 
    async def blacklist_user_error (self ,interaction :discord .Interaction ,error ):
        if isinstance (error ,app_commands .MissingPermissions ):
            error_embed =discord .Embed (
            title ="Permission Denied",
            description ="You don't have the required permissions to use this command.",
            color =discord .Color .from_str ("#ff0000")
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )
        elif isinstance (error ,app_commands .MissingRequiredArgument ):
            error_embed =discord .Embed (
            title ="Missing Arguments",
            description ="Please provide both a user and a reason.\nUsage: `/blacklist user <user> <reason>`",
            color =discord .Color .from_str ("#ff0000")
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )
        else :
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =discord .Color .from_str ("#ff0000")
            )
            await interaction .followup .send (embed =error_embed ,ephemeral =True )



    @app_commands .command (
    name ="wallet",
    description ="Blacklist a crypto wallet."
    )
    @app_commands .check (is_staff )
    async def blacklist_wallet (self ,interaction :discord .Interaction ,crypto_name :str ,wallet_address :str ):
        await interaction .response .defer ()
        try :
            already_blacklisted =False 
            if os .path .exists (DATABASE_DIR ):
                for filename in os .listdir (DATABASE_DIR ):
                    if filename .startswith (DATABASE_PREFIX )and filename .endswith (".db"):
                        db_path =os .path .join (DATABASE_DIR ,filename )
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()
                        cursor .execute (
                        "CREATE TABLE IF NOT EXISTS wallets (crypto_name TEXT, wallet_address TEXT, timestamp TEXT)"
                        )
                        cursor .execute (
                        "SELECT wallet_address FROM wallets WHERE wallet_address = ?",
                        (wallet_address ,)
                        )
                        if cursor .fetchone ()is not None :
                            already_blacklisted =True 
                            conn .close ()
                            break 
                        conn .close ()
            if already_blacklisted :
                embed =discord .Embed (
                title ="**Error**",
                description ="Address is already blacklisted.",
                color =discord .Color (int ("ff0000",16 )),
                timestamp =datetime .now (IST )
                )
                await interaction .followup .send (embed =embed ,ephemeral =True )
                return 
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"Error checking for duplicate wallet: {str (e )}",
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        try :
            timestamp ,_ =insert_wallet (crypto_name ,wallet_address )
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"An error occurred during database operation: {str (e )}",
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        log_embed =discord .Embed (
        title ="**Blacklisted Crypto Wallet**",
        color =discord .Color (int ("ff0000",16 )),
        timestamp =datetime .now (IST )
        )
        log_embed .add_field (name ="Crypto Name",value =crypto_name ,inline =False )
        log_embed .add_field (name ="Wallet Address",value =wallet_address ,inline =False )
        log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
        log_embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless"
        )

        log_channel =self .bot .get_channel (config .WALLET_BLACKLIST_CHANNEL_ID )
        if log_channel is None :
            embed =discord .Embed (
            title ="**Error**",
            description ="Log channel not found. Please check WALLET_BLACKLIST_CHANNEL_ID in config.py.",
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        await log_channel .send (embed =log_embed )

        confirmation_embed =discord .Embed (
        title ="**Success**",
        description ="Wallet successfully blacklisted.",
        color =discord .Color (int ("000001",16 )),
        timestamp =datetime .now (IST )
        )
        await interaction .followup .send (embed =confirmation_embed )

    @blacklist_wallet .error 
    async def blacklist_wallet_error (self ,interaction :discord .Interaction ,error ):
        if isinstance (error ,app_commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `/blacklist wallet <Crypto Name> <Wallet Address>`",
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
        elif isinstance (error ,app_commands .MissingPermissions ):
            embed =discord .Embed (
            title ="**Error**",
            description ="You do not have permission to use this command.",
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
        else :
            embed =discord .Embed (
            title ="**Error**",
            description ="An error occurred: "+str (error ),
            color =discord .Color (int ("ff0000",16 )),
            timestamp =datetime .now (IST )
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )



async def setup (bot :commands .Bot ):
    await bot .add_cog (BlacklistGroup (bot ))
