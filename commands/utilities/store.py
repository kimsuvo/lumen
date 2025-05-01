import re 
from discord .ext import commands 
from discord import Embed 
from functions .store_products .products_store_functions import update_services_and_products ,is_user_registered ,is_user_premium 

class PreStoreCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="store")
    async def update_store (self ,ctx ,*,store_name :str =None ):

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if not store_name or store_name .strip ()=="+store":
            store_name =""


        if not is_user_premium (ctx .author .id ):
            if re .search (r'https?://',store_name ):
                embed =Embed (
                title ="**Upgrade to Lumen Premium**",
                description ="Non‑premium users are not allowed to include links. To add links, consider activating Lumen Premium.",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 


        if len (store_name )>250 :
            embed =Embed (
            title ="**Exceeded Characters Limit**",
            description ="<:lumen_dnd:1324983165554524252> The store name must not exceed 250 characters.",
            color =0xff0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        update_services_and_products (ctx .author .id ,"store",store_name )

        embed =Embed (
        title ="**Success**",
        description =(
        f"<:lumen_online:1324983167538696303> Store information updated to: "
        f"{store_name if store_name else 'Cleared'}"
        ),
        color =0x000001 
        )
        await ctx .send (embed =embed ,delete_after =10 )

async def setup (bot ):
    await bot .add_cog (PreStoreCommands (bot ))
