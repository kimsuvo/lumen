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


IST =ZoneInfo ("Asia/Kolkata")

class CheckWallet (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="checkwallet")
    async def checkwallet (self ,ctx :commands .Context ,wallet_address :str ):
        """
        Check if the specified wallet address is blacklisted.
        This command is available to all users.
        """

        if not os .path .exists (DATABASE_DIR ):
            embed =discord .Embed (
            title ="**Error**",
            description ="No wallet database directory found.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
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
            color =0xff0000 ,
            timestamp =datetime .now (IST )
            )
            embed .add_field (name ="Crypto Name",value =crypto_name ,inline =False )
            embed .add_field (name ="Wallet Address",value =wallet_addr ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
            embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Wallet Not Found**",
            description ="This wallet address is not blacklisted.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )

    @checkwallet .error 
    async def checkwallet_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+checkwallet <Wallet Address>`",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Error**",
            description =f"An error occurred: {str (error )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (CheckWallet (bot ))
