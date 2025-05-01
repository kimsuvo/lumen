import discord 
from discord .ext import commands 
import sqlite3 
import os 
from datetime import datetime 
import config 
import pytz 


IST =pytz .timezone ('Asia/Kolkata')


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

class CheckUPI (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="checkupi")
    async def checkupi (self ,ctx :commands .Context ,upi_info :str ):
        """
        Check if a UPI ID/Number is blacklisted.
        Usage: +checkupi <UPI ID/Number>
        """


        try :
            result =find_upi_entry (upi_info )
        except Exception as e :
            embed =discord .Embed (
            title ="**UPI ID/UPI Number is not blacklisted**",
            description ="The UPI ID is not blacklisted.",
            color =SUCCESS_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 

        if result :
            upi_id ,timestamp ,_ =result 
            embed =discord .Embed (
            title ="**Blacklisted UPI Wallet**",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            embed .add_field (name ="UPI ID/Number",value =upi_id ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
            embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67b1916b&is=67b03feb&hm=7f1583b5241cc7d7bcd0bf4e2444223b9b2488a4f41581e75d735930a312bcbc&=&format=webp&quality=lossless&width=670&height=670")
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**UPI Wallet Not Blacklisted**",
            description ="This UPI ID/Number is not blacklisted.",
            color =SUCCESS_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )

    @checkupi .error 
    async def checkupi_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+checkupi <UPI ID/Number>`",
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
    await bot .add_cog (CheckUPI (bot ))
