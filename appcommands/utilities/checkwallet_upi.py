import discord 
from discord .ext import commands 
from discord import app_commands 
import sqlite3 
import os 
from datetime import datetime 
import config 
import pytz 
from zoneinfo import ZoneInfo 


IST_pytz =pytz .timezone ('Asia/Kolkata')
IST_zoneinfo =ZoneInfo ("Asia/Kolkata")


SUCCESS_COLOR =discord .Color (int ("000001",16 ))
ERROR_COLOR =discord .Color (int ("ff0000",16 ))


UPI_DATABASE_DIR ="blacklisted_wallet_upi"
UPI_DATABASE_PREFIX ="upi_wallet_"

def find_upi_entry (upi_info :str ):
    """
    Search for the UPI entry in the UPI wallet databases.
    Returns a tuple (upi_id, timestamp, db_used) if found, otherwise None.
    """
    if os .path .exists (UPI_DATABASE_DIR ):
        for filename in os .listdir (UPI_DATABASE_DIR ):
            if filename .startswith (UPI_DATABASE_PREFIX )and filename .endswith (".db"):
                db_path =os .path .join (UPI_DATABASE_DIR ,filename )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "CREATE TABLE IF NOT EXISTS upi_wallets (upi_id TEXT, timestamp TEXT)"
                    )
                    cursor .execute (
                    "SELECT upi_id, timestamp FROM upi_wallets WHERE upi_id = ?",
                    (upi_info ,)
                    )
                    row =cursor .fetchone ()
                    conn .close ()
                    if row is not None :
                        return row [0 ],row [1 ],db_path 
                except Exception as e :
                    raise Exception ("Error checking UPI database: "+str (e ))
    return None 


DATABASE_DIR ="blacklisted_wallet_crypto"
DATABASE_PREFIX ="crypto_wallet_"

class Check (commands .GroupCog ,name ="check"):
    """Group of slash commands to check UPI and wallet blacklists."""

    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @app_commands .command (name ="upi",description ="Check if a UPI ID/Number is blacklisted")
    async def upi (self ,interaction :discord .Interaction ,upi_info :str ):
        """
        Check if a UPI ID/Number is blacklisted.
        Usage: /check upi <upi_info>
        """
        try :
            result =find_upi_entry (upi_info )
        except Exception as e :
            embed =discord .Embed (
            title ="**UPI ID/UPI Number is not blacklisted**",
            description ="The UPI ID is not blacklisted.",
            color =SUCCESS_COLOR ,
            timestamp =datetime .now (IST_pytz )
            )
            await interaction .response .send_message (embed =embed )
            return 

        if result :
            upi_id ,timestamp ,_ =result 
            embed =discord .Embed (
            title ="**Blacklisted UPI Wallet**",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST_pytz )
            )
            embed .add_field (name ="UPI ID/Number",value =upi_id ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
            embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")
            await interaction .response .send_message (embed =embed )
        else :
            embed =discord .Embed (
            title ="**UPI Wallet Not Blacklisted**",
            description ="This UPI ID/Number is not blacklisted.",
            color =SUCCESS_COLOR ,
            timestamp =datetime .now (IST_pytz )
            )
            await interaction .response .send_message (embed =embed )

    @app_commands .command (name ="wallet",description ="Check if a wallet address is blacklisted")
    async def wallet (self ,interaction :discord .Interaction ,wallet_address :str ):
        """
        Check if the specified wallet address is blacklisted.
        Usage: /check wallet <wallet_address>
        """
        if not os .path .exists (DATABASE_DIR ):
            embed =discord .Embed (
            title ="**Error**",
            description ="No wallet database directory found.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST_zoneinfo )
            )
            await interaction .response .send_message (embed =embed )
            return 

        wallet_found =False 
        record =None 


        for filename in os .listdir (DATABASE_DIR ):
            if filename .startswith (DATABASE_PREFIX )and filename .endswith (".db"):
                db_path =os .path .join (DATABASE_DIR ,filename )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "CREATE TABLE IF NOT EXISTS wallets (crypto_name TEXT, wallet_address TEXT, timestamp TEXT)"
                    )
                    cursor .execute (
                    "SELECT crypto_name, wallet_address, timestamp FROM wallets WHERE wallet_address = ?",
                    (wallet_address ,)
                    )
                    record =cursor .fetchone ()
                    conn .close ()
                    if record is not None :
                        wallet_found =True 
                        break 
                except Exception :
                    continue 

        if wallet_found and record is not None :
            crypto_name ,wallet_addr ,timestamp =record 
            embed =discord .Embed (
            title ="**Blacklisted Wallet Found**",
            description ="This wallet address is blacklisted.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST_zoneinfo )
            )
            embed .add_field (name ="Crypto Name",value =crypto_name ,inline =False )
            embed .add_field (name ="Wallet Address",value =wallet_addr ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
            embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")
            await interaction .response .send_message (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Wallet Not Found**",
            description ="This wallet address is not blacklisted.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST_zoneinfo )
            )
            await interaction .response .send_message (embed =embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (Check (bot ))
