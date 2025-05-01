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

class RemoveWalletBL (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="removeblcr")
    async def removewalletbl (self ,ctx :commands .Context ,wallet_address :str ):

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


        if not os .path .exists (DATABASE_DIR ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Database directory does not exist.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 

        wallet_found =False 


        for filename in os .listdir (DATABASE_DIR ):
            if filename .startswith (DATABASE_PREFIX )and filename .endswith (".db"):
                db_path =os .path .join (DATABASE_DIR ,filename )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "CREATE TABLE IF NOT EXISTS wallets (crypto_name TEXT, wallet_address TEXT, timestamp TEXT)"
                    )

                    cursor .execute ("SELECT * FROM wallets WHERE wallet_address = ?",(wallet_address ,))
                    row =cursor .fetchone ()
                    if row is not None :
                        wallet_found =True 

                        cursor .execute ("DELETE FROM wallets WHERE wallet_address = ?",(wallet_address ,))
                        conn .commit ()
                    conn .close ()
                except Exception :

                    continue 

        if not wallet_found :
            embed =discord .Embed (
            title ="**Error**",
            description ="Wallet address not found in any database.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 


        embed =discord .Embed (
        title ="**Success**",
        description ="Wallet address has been removed from the blacklist.",
        color =SUCCESS_COLOR ,
        timestamp =datetime .now (IST )
        )
        await ctx .send (embed =embed )

    @removewalletbl .error 
    async def removewalletbl_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+removewalletbl <Wallet Address>`",
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
    await bot .add_cog (RemoveWalletBL (bot ))
