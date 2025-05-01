import discord 
from discord import Embed 
from discord .ext import commands 
import datetime 
from functions .status_functions .status_db import update_user_status ,get_user_status ,remove_user_status 
from functions .status_functions .user_utils import is_user_registered ,is_user_premium 

class AddStatus (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def status (self ,ctx ,*args ):
        user =ctx .author 


        if not is_user_registered (user .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if len (args )==0 :
            remove_user_status (user .id )
            embed =Embed (
            title ="<:lumen_online:1324983167538696303> **Status Removed**",
            description ="Your status has been removed successfully.",
            color =0x000001 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 

        status_message =" ".join (args )


        if len (status_message )>150 :
            embed =Embed (
            title ="<:lumen_dnd:1324983165554524252> **Exceeded Characters Limit**",
            description ="Your status message cannot exceed 150 characters. Please shorten your message.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        current_status ,status_update_block ,last_updated =get_user_status (user .id ,include_last_updated =True )
        if status_update_block =='yes':
            embed =Embed (
            title ="<:lumen_dnd:1324983165554524252> **Status Update Blocked**",
            description ="Your status update is blocked. You cannot change your status at the moment.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if not is_user_premium (user .id ):
            if last_updated :
                try :
                    last_updated_dt =datetime .datetime .fromisoformat (last_updated )
                except ValueError :
                    last_updated_dt =datetime .datetime .strptime (last_updated ,"%Y-%m-%d %H:%M:%S")
                now =datetime .datetime .now ()
                if now -last_updated_dt <datetime .timedelta (hours =24 ):
                    embed =Embed (
                    title ="**Upgrade to Lumen Premium**",
                    description ="You can only update your status once every 24 hours. Upgrade to Lumen Premium for unlimited updates.",
                    color =0xff0000 
                    )
                    await ctx .send (embed =embed ,delete_after =10 )
                    return 


        update_user_status (user .id ,status_message ,status_update_block ='no',include_last_updated =True )
        success_embed =Embed (
        title ="<:lumen_online:1324983167538696303> **Success**",
        description =f"Your status has been updated to: **{status_message }**.",
        color =0x000001 
        )
        await ctx .send (embed =success_embed ,delete_after =10 )

async def setup (bot ):
    await bot .add_cog (AddStatus (bot ))
