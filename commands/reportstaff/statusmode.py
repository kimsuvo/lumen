import discord 
from discord .ext import commands 
from config import REPORT_STAFF_ROLE 
from functions .status_functions .status_db import get_user_status ,update_user_status 

class StatusMode (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def statusmode (self ,ctx ,target_user :discord .Member ):
        """Toggles the status update block for a user."""

        if any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ):

            _ ,status_update_block =get_user_status (target_user .id ,include_last_updated =False )

            new_flag ='no'if status_update_block =='yes'else 'yes'

            update_user_status (target_user .id ,'',status_update_block =new_flag ,include_last_updated =False )

            success_embed =discord .Embed (
            title ="<:lumen_online:1324983167538696303> **Success**",
            description =f"Status Update Block for **{target_user .name }** has been set to **{new_flag }**.",
            color =0x000001 
            )
            await ctx .send (embed =success_embed )
        else :
            error_embed =discord .Embed (
            title ="<:lumen_dnd:1324983165554524252> **Permission Denied**",
            description ="You do not have permission to use this command.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed )


async def setup (bot ):
    await bot .add_cog (StatusMode (bot ))
