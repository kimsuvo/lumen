import discord 
from discord .ext import commands 
import sqlite3 
import logging 
import os 
from config import RECOVERY_STAFF_ROLE_ID 

class PendingRecovery (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def viewrecoveries (self ,ctx ):
        try :
            required_role_ids =RECOVERY_STAFF_ROLE_ID 
            if not any (role .id in required_role_ids for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="Permission Denied",
                description ="You do not have the required role to view pending recoveries.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 


            directory ="recoverydatabase"
            if not os .path .exists (directory ):
                embed =discord .Embed (
                title ="Error",
                description =f"The directory `{directory }` does not exist.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 

            all_rows =[]

            for filename in os .listdir (directory ):
                if filename .endswith (".db"):
                    db_path =os .path .join (directory ,filename )
                    try :
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()
                        cursor .execute ('SELECT * FROM pending_recovery')
                        rows =cursor .fetchall ()
                        conn .close ()

                        all_rows .extend (rows )
                    except Exception as db_error :
                        logging .error (f"Error accessing database {filename }: {db_error }")

            if not all_rows :
                embed =discord .Embed (
                title ="No Pending Recoveries",
                description ="No pending recovery requests found in any database.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 


            chunks =[all_rows [i :i +3 ]for i in range (0 ,len (all_rows ),3 )]
            total_pages =len (chunks )

            for page_number ,chunk in enumerate (chunks ,start =1 ):
                embed =discord .Embed (
                title =f"Pending Recoveries ({page_number }/{total_pages })",
                color =0xfbb03b 
                )
                for row in chunk :
                    embed .add_field (name ="Recovery ID",value =f'```{row [0 ]}```',inline =False )
                    embed .add_field (name ="Previous User ID",value =f'`{row [1 ]}`',inline =True )
                    embed .add_field (name ="New User ID",value =f'`{row [2 ]}`',inline =True )
                    embed .add_field (name ="Username",value =f'`{row [3 ]}`',inline =False )

                await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Error Viewing Recoveries",
            description =f"An error occurred while retrieving the recovery requests: `{e }`",
            color =0xff0000 
            )
            logging .error (f"Error viewing recoveries: {e }")
            await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (PendingRecovery (bot ))