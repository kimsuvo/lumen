import re 
from discord .ext import commands 
from discord import Embed 
from functions .store_products .products_store_functions import update_services_and_products ,is_user_registered ,is_user_premium 

class PreProductsCommands (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="products")
    async def update_products (self ,ctx ,*,products_info :str =None ):

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if products_info =="+products"or not products_info :
            products_info =[]
        else :

            products =[product .strip ()for product in products_info .split (",")]


            if any ("http://"in product or "https://"in product for product in products ):
                embed =Embed (
                title ="**Invalid Product Info**",
                description ="<:lumen_dnd:1324983165554524252> Links are not allowed in product names.",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 


            if any (len (product )>150 for product in products ):
                embed =Embed (
                title ="**Exceeding Characters Limit**",
                description ="<:lumen_dnd:1324983165554524252> Each product name must not exceed 150 characters.",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 


            max_products =5 if is_user_premium (ctx .author .id )else 3 
            if len (products )>max_products :
                if not is_user_premium (ctx .author .id ):
                    embed =Embed (
                    title ="**Upgrade to Lumen Premium**",
                    description =(
                    "You can only register up to 3 products with your current account. "
                    "To add up to 6 products, consider activating Lumen Premium."
                    ),
                    color =0xff0000 
                    )
                else :
                    embed =Embed (
                    title ="**Error**",
                    description =f"<:lumen_dnd:1324983165554524252> You can register up to {max_products } products only.",
                    color =0xff0000 
                    )
                await ctx .send (embed =embed ,delete_after =10 )
                return 

            products_info =products 


        update_services_and_products (ctx .author .id ,"products",products_info )


        embed =Embed (
        title ="**Success**",
        description =(
        f"<:lumen_online:1324983167538696303> Products updated to:\n"+
        "\n".join ([f"- {product }"for product in products_info ])
        if products_info else "<:lumen_online:1324983167538696303> No products added."
        ),
        color =0x000001 
        )
        await ctx .send (embed =embed ,delete_after =10 )

async def setup (bot ):
    await bot .add_cog (PreProductsCommands (bot ))
