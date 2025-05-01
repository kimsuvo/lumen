

import asyncio 
from datetime import datetime 

import discord 
from discord import Embed 
from discord .ext import commands 
from discord .ext .commands import BucketType 
import pytz 


from functions .password_functions .changepassword_functions import is_user_registered ,ChangePasswordView 

class PreChangePassword (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command (
    name ="changepassword",
    aliases =["cpwd"],
    help ="Change or reset your account password securely."
    )
    async def change_password (self ,ctx ):

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        kolkata_tz =pytz .timezone ("Asia/Kolkata")
        current_time_kolkata =datetime .now (kolkata_tz )


        embed =discord .Embed (
        title ="**Manage Your Password**",
        description =(
        "Choose an option below to **update** or **reset** your password securely.\n\n"
        "**__Precautions__**:\n"
        "-# 1. **Do not share your password** with anyone.\n"
        "-# 2. Ensure your password is **unique** and not used elsewhere.\n"
        "-# 3. Use a combination of **letters, numbers, and special characters** for better security.\n"
        "-# 4. **Avoid clicking on suspicious links** or providing your credentials on untrusted websites.\n\n"
        "**__Your security is our priority!__**\n"
        "If you didn’t request a password change, **report immediately** to [Lumen Support Server](https://discord.gg/lumenreport)."
        ),
        color =0x000001 
        )
        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
        embed .set_footer (text ="For security reasons, this interaction is private.")
        embed .timestamp =current_time_kolkata 

        view =ChangePasswordView (self .bot )


        confirmation_embed =discord .Embed (
        title ="**Password Change Request**",
        description ="Please check your DMs for password management options.",
        color =0x000001 
        )

        error_embed =discord .Embed (
        title ="Error",
        description ="I couldn't send you a DM. Please enable DMs and try again.",
        color =0xff0000 
        )

        try :

            await ctx .author .send (embed =embed ,view =view )

            await ctx .reply (embed =confirmation_embed ,delete_after =10 )

            await asyncio .sleep (1 )
            await ctx .message .delete ()
        except discord .Forbidden :
            await ctx .reply (embed =error_embed ,delete_after =10 )

    @change_password .error 
    async def change_password_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):
            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =f"You're on cooldown! Please try again in {error .retry_after :.1f} seconds.",
            color =0xff0000 ,
            timestamp =discord .utils .utcnow ()
            )
            cooldown_embed .set_footer (
            text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :
            raise error 


async def setup (bot ):
    await bot .add_cog (PreChangePassword (bot ))
