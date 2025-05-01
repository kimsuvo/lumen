import discord 
from discord .ext import commands 
import sqlite3 
import os 
from datetime import datetime 
from zoneinfo import ZoneInfo 
import config 


SUCCESS_COLOR =discord .Color (int ("000001",16 ))
ERROR_COLOR =discord .Color (int ("ff0000",16 ))


DATABASE_DIR ="blacklisted_wallet_crypto"
DATABASE_PREFIX ="crypto_wallet_"
DATABASE_LIMIT =20000 


IST =ZoneInfo ("Asia/Kolkata")

def get_database_path ()->str :
    """Return a database path that has less than DATABASE_LIMIT entries,
    or a new database if all current ones are full."""

    if not os .path .exists (DATABASE_DIR ):
        try :
            os .makedirs (DATABASE_DIR )
        except Exception as e :
            raise Exception ("Error creating directory for databases: "+str (e ))

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

class WalletBlacklist (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="blcrwallet")
    async def blcrwallet (self ,ctx :commands .Context ,crypto_name :str ,wallet_address :str ):

        try :
            required_role_ids =config .REPORT_STAFF_ROLE 
            if not any (role .id in required_role_ids for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="**Error**",
                description ="You do not have permission to use this command.",
                color =ERROR_COLOR ,
                timestamp =datetime .now (IST )
                )
                await ctx .send (embed =embed )
                return 
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"Error verifying roles: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 


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
                color =ERROR_COLOR ,
                timestamp =datetime .now (IST )
                )
                await ctx .send (embed =embed )
                return 
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"Error checking for duplicate wallet: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 


        try :
            timestamp ,_ =insert_wallet (crypto_name ,wallet_address )
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"An error occurred during database operation: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 


        log_embed =discord .Embed (
        title ="**Blacklisted Crypto Wallet**",
        color =ERROR_COLOR ,
        timestamp =datetime .now (IST )
        )
        log_embed .add_field (name ="Crypto Name",value =crypto_name ,inline =False )
        log_embed .add_field (name ="Wallet Address",value =wallet_address ,inline =False )
        log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
        log_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")

        log_channel =self .bot .get_channel (config .WALLET_BLACKLIST_CHANNEL_ID )
        if log_channel is None :
            embed =discord .Embed (
            title ="**Error**",
            description ="Error: Log channel not found. Please check WALLET_BLACKLIST_CHANNEL_ID in config.py.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 

        await log_channel .send (embed =log_embed )


        confirmation_embed =discord .Embed (
        title ="**Success**",
        description ="Wallet successfully blacklisted.",
        color =SUCCESS_COLOR ,
        timestamp =datetime .now (IST )
        )
        await ctx .send (embed =confirmation_embed )

    @blcrwallet .error 
    async def blcrwallet_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+blcrwallet <Crypto Name> <Wallet Address>`",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Error**",
            description ="An error occurred: "+str (error ),
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (WalletBlacklist (bot ))
