import discord 
from discord .ext import commands 
import sqlite3 
import os 
from datetime import datetime 
from zoneinfo import ZoneInfo 
import config 


SUCCESS_COLOR =discord .Color (int ("000001",16 ))
ERROR_COLOR =discord .Color (int ("ff0000",16 ))


UPI_DATABASE_DIR ="blacklisted_wallet_upi"
UPI_DATABASE_PREFIX ="upi_wallet_"
DATABASE_LIMIT =20000 

def get_database_path_upi ()->str :
    """
    Return a database path that has less than DATABASE_LIMIT entries,
    or a new database if all current ones are full (for UPI wallets).
    """
    if not os .path .exists (UPI_DATABASE_DIR ):
        try :
            os .makedirs (UPI_DATABASE_DIR )
        except Exception as e :
            raise Exception ("Error creating directory for UPI databases: "+str (e ))

    db_index =1 
    while True :
        db_path =os .path .join (UPI_DATABASE_DIR ,f"{UPI_DATABASE_PREFIX }{db_index }.db")
        if not os .path .exists (db_path ):
            return db_path 
        else :
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute (
                "CREATE TABLE IF NOT EXISTS upi_wallets (upi_id TEXT, timestamp TEXT)"
                )
                conn .commit ()
                cursor .execute ("SELECT COUNT(*) FROM upi_wallets")
                count =cursor .fetchone ()[0 ]
                conn .close ()
            except sqlite3 .Error as e :
                raise Exception ("Error accessing UPI database: "+str (e ))

            if count <DATABASE_LIMIT :
                return db_path 
            else :
                db_index +=1 

def insert_wallet_upi (upi_id :str )->tuple [str ,str ]:
    """
    Insert the UPI wallet info into the appropriate database and return the timestamp and db used.
    """
    try :
        db_path =get_database_path_upi ()
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute (
        "CREATE TABLE IF NOT EXISTS upi_wallets (upi_id TEXT, timestamp TEXT)"
        )
        timestamp =datetime .now (ZoneInfo ("Asia/Kolkata")).strftime ("%Y-%m-%d %H:%M:%S")
        cursor .execute (
        "INSERT INTO upi_wallets (upi_id, timestamp) VALUES (?, ?)",
        (upi_id ,timestamp )
        )
        conn .commit ()
        conn .close ()
        return timestamp ,db_path 
    except sqlite3 .Error as e :
        raise Exception ("Database insertion error: "+str (e ))
    except Exception as e :
        raise Exception ("Unexpected error during UPI database operation: "+str (e ))

class UPIWalletBlacklist (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="blupiwallet")
    async def blupiwallet (self ,ctx :commands .Context ,upi_info :str ):
        """
        Blacklist a UPI ID/Number.
        Usage: +blupiwallet <UPI ID/Number>
        """

        try :
            required_role_ids =config .REPORT_STAFF_ROLE 
            if not any (role .id in required_role_ids for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="**Error**",
                description ="You do not have permission to use this command.",
                color =ERROR_COLOR ,
                timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
                )
                await ctx .send (embed =embed )
                return 
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"Error verifying roles: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )
            return 


        try :
            already_blacklisted =False 
            if os .path .exists (UPI_DATABASE_DIR ):
                for filename in os .listdir (UPI_DATABASE_DIR ):
                    if filename .startswith (UPI_DATABASE_PREFIX )and filename .endswith (".db"):
                        db_path =os .path .join (UPI_DATABASE_DIR ,filename )
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()
                        cursor .execute (
                        "CREATE TABLE IF NOT EXISTS upi_wallets (upi_id TEXT, timestamp TEXT)"
                        )
                        cursor .execute (
                        "SELECT upi_id FROM upi_wallets WHERE upi_id = ?",
                        (upi_info ,)
                        )
                        if cursor .fetchone ()is not None :
                            already_blacklisted =True 
                            conn .close ()
                            break 
                        conn .close ()
            if already_blacklisted :
                embed =discord .Embed (
                title ="**Error**",
                description ="UPI ID/Number is already blacklisted.",
                color =ERROR_COLOR ,
                timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
                )
                await ctx .send (embed =embed )
                return 
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"Error checking for duplicate UPI: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )
            return 


        try :
            timestamp ,db_used =insert_wallet_upi (upi_info )
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"An error occurred during UPI database operation: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )
            return 


        log_embed =discord .Embed (
        title ="**Blacklisted UPI Wallet**",
        color =ERROR_COLOR ,
        timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
        )
        log_embed .add_field (name ="UPI ID/Number",value =upi_info ,inline =False )
        log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
        log_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")



        log_channel =self .bot .get_channel (config .WALLET_BLACKLIST_CHANNEL_ID )
        if log_channel is None :
            embed =discord .Embed (
            title ="**Error**",
            description ="Error: Log channel not found. Please check WALLET_BLACKLIST_CHANNEL_ID in config.py.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )
            return 

        await log_channel .send (embed =log_embed )


        confirmation_embed =discord .Embed (
        title ="**Success**",
        description ="UPI Wallet successfully blacklisted.",
        color =SUCCESS_COLOR ,
        timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
        )
        await ctx .send (embed =confirmation_embed )

    @blupiwallet .error 
    async def blupiwallet_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+blupiwallet <UPI ID/Number>`",
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Error**",
            description ="An error occurred: "+str (error ),
            color =ERROR_COLOR ,
            timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
            )
            await ctx .send (embed =embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (UPIWalletBlacklist (bot ))
