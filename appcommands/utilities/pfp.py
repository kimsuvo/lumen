import discord 
from discord import app_commands 
from discord .ext import commands 


from functions .image_functions .image import get_user_data ,update_image_data ,ensure_user_exists 
from functions .image_functions .common_functions import is_user_registered 
from functions .premium_functions .premium_user_functions import is_user_premium 

class PfpCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @app_commands .command (name ="pfp",description ="Update your profile thumbnail URL")
    @app_commands .describe (url ="Your thumbnail URL. Provide an empty value to reset.")
    async def pfp (self ,interaction :discord .Interaction ,url :str =None ):

        user_data =get_user_data (str (interaction .user .id ))


        if not is_user_registered (interaction .user .id ):
            embed =discord .Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not is_user_premium (interaction .user .id ):
            embed =discord .Embed (
            title ="**Upgrade to Lumen Premium**",
            description ="<:lumen_dnd:1324983165554524252> This is a premium feature. Consider upgrading to Lumen premium.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if user_data and user_data .get ("DWC","").lower ()=="yes":
            embed =discord .Embed (
            title ="**Action Blocked**",
            description ="<:lumen_dnd:1324983165554524252> Changes are not allowed because your DWC setting is enabled.",
            color =0xFBB03B 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if url =="+thumbnail"or not url :
            url =""
        elif len (url )>400 :
            embed =discord .Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> The URL is too long. It must be less than 400 characters.",
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


        update_image_data (str (interaction .user .id ),"thumbnail",url )

        embed =discord .Embed (
        title ="**Success**",
        description =(f"<:lumen_online:1324983167538696303> Thumbnail URL updated to: {url }"
        if url else "<:lumen_online:1324983167538696303> Thumbnail URL reset to default."),
        color =0x000001 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (PfpCommands (bot ))
