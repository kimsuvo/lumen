import discord 
from discord .ext import commands 
import sqlite3 
import os 
from datetime import datetime 
import pytz 
import config 


IST =pytz .timezone ("Asia/Kolkata")


SUCCESS_COLOR =discord .Color (int ("000001",16 ))
ERROR_COLOR =discord .Color (int ("ff0000",16 ))


UPI_DATABASE_DIR ="blacklisted_wallet_upi"
UPI_DATABASE_PREFIX ="upi_wallet_"

def remove_upi_entry (upi_info :str ):
    """
    Search for and remove the UPI entry from the UPI wallet databases.
    Returns a tuple (upi_id, original_timestamp, db_used) if removed successfully,
    or None if the UPI was not found.
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
                    if row is not None :

                        cursor .execute (
                        "DELETE FROM upi_wallets WHERE upi_id = ?",
                        (upi_info ,)
                        )
                        conn .commit ()
                        conn .close ()
                        return row [0 ],row [1 ],db_path 
                    conn .close ()
                except Exception as e :
                    raise Exception ("Error removing UPI entry from database: "+str (e ))
    return None 

class RemoveUPI (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="removeblupi")
    async def removeblupi (self ,ctx :commands .Context ,upi_info :str ):
        """
        Remove a blacklisted UPI ID/Number.
        Usage: +removeblupi <UPI ID/Number>
        """

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
            removed_entry =remove_upi_entry (upi_info )
        except Exception as e :
            embed =discord .Embed (
            title ="**Error**",
            description =f"An error occurred while removing the UPI entry: {str (e )}",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 

        if removed_entry is None :
            embed =discord .Embed (
            title ="**Error**",
            description ="The UPI ID/Number is not blacklisted.",
            color =ERROR_COLOR ,
            timestamp =datetime .now (IST )
            )
            await ctx .send (embed =embed )
            return 

        upi_id ,original_timestamp ,_ =removed_entry 
        removal_timestamp =datetime .now (IST ).strftime ("%Y-%m-%d %H:%M:%S")


























        confirmation_embed =discord .Embed (
        title ="**Success**",
        description ="UPI ID/UPI Number successfully removed from blacklist.",
        color =SUCCESS_COLOR ,
        timestamp =datetime .now (IST )
        )
        await ctx .send (embed =confirmation_embed )

    @removeblupi .error 
    async def removeblupi_error (self ,ctx :commands .Context ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Error**",
            description ="Missing required argument. Usage: `+removeblupi <UPI ID/Number>`",
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
    await bot .add_cog (RemoveUPI (bot ))
