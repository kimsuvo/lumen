import discord 
from discord import app_commands 
from discord .ext import commands 


from functions .image_functions .image import get_user_data ,update_image_data ,ensure_user_exists 
from functions .image_functions .common_functions import is_user_registered 

class BannerCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @app_commands .command (name ="banner",description ="Update your banner image URL")
    @app_commands .describe (url ="Your banner image URL. Provide an empty value to reset.")
    async def banner (self ,interaction :discord .Interaction ,url :str =None ):
        if not is_user_registered (interaction .user .id ):
            embed =discord .Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        user_data =get_user_data (str (interaction .user .id ))
        if user_data and user_data .get ("DWC","").lower ()=="yes":
            embed =discord .Embed (
            title ="**Action Blocked**",
            description ="<:lumen_dnd:1324983165554524252> Changes are not allowed because your DWC setting is enabled.",
            color =0xFBB03B 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if url =="+image"or not url :
            url =""
        elif len (url )>400 :
            embed =discord .Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> The provided URL is too long. Please provide a URL with fewer than 400 characters.",
            color =0xFBB03B 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 
        elif not (url .startswith ("http://")or url .startswith ("https://")):
            embed =discord .Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> Please provide a valid URL starting with `http://` or `https://`.",
            color =0xFBB03B 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        ensure_user_exists (str (interaction .user .id ),"image",url )
        update_image_data (str (interaction .user .id ),"image",url )

        embed =discord .Embed (
        title ="**Success**",
        description =(f"<:lumen_online:1324983167538696303> Image URL updated to: {url }"
        if url else "<:lumen_online:1324983167538696303> Image URL reset to default."),
        color =0x000001 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (BannerCommands (bot ))
