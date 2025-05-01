import discord 
from discord .ext import commands 
from config import REPORT_STAFF_ROLE 
from functions .status_functions .status_db import update_user_status 

class LockStatus (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def lockstatus (self ,ctx ,user :discord .User ,*,status_message ):

        if not any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="Error",
            description ="You do not have permission to use this command.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
            return 


        try :

            update_user_status (user .id ,status_message ,status_update_block ='yes',include_last_updated =False )
            embed =discord .Embed (
            title ="**Success**",
            description =f"Status for {user .mention } has been updated to: **{status_message }**",
            color =0x000001 
            )
        except Exception as e :
            embed =discord .Embed (
            title ="Error",
            description =f"Failed to update status: {str (e )}",
            color =discord .Color .red ()
            )
        await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (LockStatus (bot ))
