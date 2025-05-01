

import os 
import sqlite3 
from discord .ext import commands 
from discord import Embed 


from functions .image_functions .image import get_user_data ,update_image_data ,ensure_user_exists 
from functions .image_functions .common_functions import is_user_registered 

class PreBannerCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="banner")
    async def set_image (self ,ctx ,url :str =None ):
        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 

        user_data =get_user_data (str (ctx .author .id ))
        if user_data and user_data .get ("DWC","").lower ()=="yes":
            embed =Embed (
            title ="**Action Blocked**",
            description ="<:lumen_dnd:1324983165554524252> Changes are not allowed because your DWC setting is enabled.",
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if url =="+image"or not url :
            url =""
        elif len (url )>400 :
            embed =Embed (
            title ="**Error**",
            description ="<:lumen_dnd:1324983165554524252> The provided URL is too long. Please provide a URL with fewer than 400 characters.",
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


        ensure_user_exists (str (ctx .author .id ),"image",url )
        update_image_data (str (ctx .author .id ),"image",url )

        embed =Embed (
        title ="**Success**",
        description =(f"<:lumen_online:1324983167538696303> Image URL updated to: {url }"
        if url else "<:lumen_online:1324983167538696303> Image URL reset to default."),
        color =0x000001 
        )
        await ctx .send (embed =embed ,delete_after =10 )

async def setup (bot ):
    await bot .add_cog (PreBannerCommands (bot ))
