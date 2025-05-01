import re 
import discord 
from discord import Embed ,app_commands 
from discord .ext import commands 
import sqlite3 


from functions .store_products .products_store_functions import (
update_services_and_products ,
is_user_registered as is_registered_store ,
is_user_premium as is_premium_store ,
)


from functions .storebutton_functions .storebutton import (
is_user_registered as is_registered_button ,
is_user_premium as is_premium_button ,
get_database_connection ,
)

class Store (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 


    store =app_commands .Group (name ="store",description ="Store commands.")

    @store .command (name ="update",description ="Update your store information")
    @app_commands .describe (store_name ="Your store name. Use '+store' to clear your store info")
    async def update (self ,interaction :discord .Interaction ,store_name :str =None ):

        if not is_registered_store (interaction .user .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not store_name or store_name .strip ()=="+store":
            store_name =""


        if not is_premium_store (interaction .user .id ):
            if re .search (r'https?://',store_name ):
                embed =Embed (
                title ="**Upgrade to Lumen Premium**",
                description ="Non‑premium users are not allowed to include links. To add links, consider activating Lumen Premium.",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 


        if len (store_name )>250 :
            embed =Embed (
            title ="**Exceeded Characters Limit**",
            description ="<:lumen_dnd:1324983165554524252> The store name must not exceed 250 characters.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        update_services_and_products (interaction .user .id ,"store",store_name )

        embed =Embed (
        title ="**Success**",
        description =(
        f"<:lumen_online:1324983167538696303> Store information updated to: "
        f"{store_name if store_name else 'Cleared'}"
        ),
        color =0x000001 
        )
        await interaction .response .send_message (embed =embed )

    @store .command (name ="button",description ="Store your button state as on or off.")
    @app_commands .describe (choice ="Choose 'on' to enable or 'off' to disable")
    @app_commands .choices (choice =[
    app_commands .Choice (name ="on",value ="on"),
    app_commands .Choice (name ="off",value ="off")
    ])
    async def button (self ,interaction :discord .Interaction ,choice :str ):
        """
        Slash command usage: /store button choice:on or /store button choice:off

        This command checks if the user is registered and premium.
        It stores "yes" if the choice is "on", otherwise it stores "no".
        The response is always sent ephemerally.
        """

        if not is_registered_button (interaction .user .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not is_premium_button (interaction .user .id ):
            embed =Embed (
            title ="**Upgrade to Lumen Premium**",
            description ="This command is only available to premium users. Consider upgrading to Lumen Premium.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        store_value ="yes"if choice .lower ()=="on"else "no"


        try :
            conn =get_database_connection ()
        except Exception as e :
            embed =Embed (
            title ="Error",
            description =f"Could not establish a database connection. ({e })",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        try :
            cursor =conn .cursor ()
            user_id =str (interaction .user .id )

            try :
                cursor .execute ("INSERT INTO buttons (user_id, storebutton) VALUES (?, ?)",
                (user_id ,store_value ))
            except sqlite3 .IntegrityError :
                cursor .execute ("UPDATE buttons SET storebutton = ? WHERE user_id = ?",
                (store_value ,user_id ))

            conn .commit ()
        except Exception as e :
            embed =Embed (
            title ="Error",
            description =f"Database operation failed: {e }",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 
        finally :
            conn .close ()


        embed =Embed (
        title ="Success",
        description =f"Your button state has been stored as **{store_value }**.",
        color =0x000001 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (Store (bot ))
