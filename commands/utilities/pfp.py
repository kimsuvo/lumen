

from discord .ext import commands 
from discord import Embed 


from functions .image_functions .image import get_user_data ,update_image_data ,ensure_user_exists 
from functions .image_functions .common_functions import is_user_registered 
from functions .premium_functions .premium_user_functions import is_user_premium 

class PrePfpCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="pfp")
    async def set_thumbnail (self ,ctx ,url :str =None ):

        user_data =get_user_data (str (ctx .author .id ))


        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if not is_user_premium (ctx .author .id ):
            embed =Embed (
            title ="**Upgrade to Lumen Premium**",
            description ="<:lumen_dnd:1324983165554524252> This is a premium feature. Consider upgrading to Lumen premium.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if user_data and user_data .get ("DWC","").lower ()=="yes":
            embed =Embed (
            title ="**Action Blocked**",
            description ="<:lumen_dnd:1324983165554524252> Changes are not allowed because your DWC setting is enabled.",
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if url =="+thumbnail"or not url :
            url =""
        elif len (url )>400 :
            embed =Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> The URL is too long. It must be less than 400 characters.",
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 
        elif not (url .startswith ("http://")or url .startswith ("https://")):
            embed =Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> Please provide a valid URL starting with `http://` or `https://`.",
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        update_image_data (str (ctx .author .id ),"thumbnail",url )

        embed =Embed (
        title ="**Success**",
        description =(f"<:lumen_online:1324983167538696303> Thumbnail URL updated to: {url }"
        if url else "<:lumen_online:1324983167538696303> Thumbnail URL reset to default."),
        color =0x000001 
        )
        await ctx .send (embed =embed ,delete_after =10 )

async def setup (bot ):
    await bot .add_cog (PrePfpCommands (bot ))
