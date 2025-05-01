from typing import Optional 
import discord 
from discord import app_commands 
from discord .ext import commands 
from functions .store_products .products_store_functions import update_services_and_products ,is_user_registered ,is_user_premium 

class ProductsCommands (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @app_commands .command (
    name ="products",
    description ="Update your products list. Provide 3 required products and up to 2 extra products for premium users."
    )
    @app_commands .describe (
    product1 ="The first product (required)",
    product2 ="The second product (required)",
    product3 ="The third product (required)",
    product4 ="Optional: Fourth product (premium users only)",
    product5 ="Optional: Fifth product (premium users only)"
    )
    async def products (
    self ,
    interaction :discord .Interaction ,
    product1 :str ,
    product2 :str ,
    product3 :str ,
    product4 :Optional [str ]=None ,
    product5 :Optional [str ]=None 
    ):

        if not is_user_registered (interaction .user .id ):
            embed =discord .Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        products =[product1 .strip (),product2 .strip (),product3 .strip ()]
        if product4 :
            products .append (product4 .strip ())
        if product5 :
            products .append (product5 .strip ())


        if any ("http://"in product or "https://"in product for product in products ):
            embed =discord .Embed (
            title ="**Invalid Product Info**",
            description ="<:lumen_dnd:1324983165554524252> Links are not allowed in product names.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if any (len (product )>150 for product in products ):
            embed =discord .Embed (
            title ="**Exceeding Characters Limit**",
            description ="<:lumen_dnd:1324983165554524252> Each product name must not exceed 150 characters.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        max_products =5 if is_user_premium (interaction .user .id )else 3 
        if len (products )>max_products :
            if not is_user_premium (interaction .user .id ):
                embed =discord .Embed (
                title ="**Upgrade to Lumen Premium**",
                description =(
                "You can only register up to 3 products with your current account. "
                "To add up to 6 products, consider activating Lumen Premium."
                ),
                color =0xff0000 
                )
            else :
                embed =discord .Embed (
                title ="**Error**",
                description =f"<:lumen_dnd:1324983165554524252> You can register up to {max_products } products only.",
                color =0xff0000 
                )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        update_services_and_products (interaction .user .id ,"products",products )


        embed =discord .Embed (
        title ="**Success**",
        description =(
        "<:lumen_online:1324983167538696303> Products updated to:\n"+
        "\n".join ([f"- {product }"for product in products ])
        if products else "<:lumen_online:1324983167538696303> No products added."
        ),
        color =0x000001 
        )
        await interaction .response .send_message (embed =embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (ProductsCommands (bot ))
