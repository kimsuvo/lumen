import discord 
from discord .ext import commands 
from discord import Embed 
import sqlite3 


from functions .storebutton_functions .storebutton import (
is_user_premium ,
is_user_registered ,
get_database_connection ,
)

class PreStoreButton (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def storebutton (self ,ctx ,arg :str ):
        """
        Command usage: +storebutton <on>
        If the argument is "on" (case-insensitive), store "yes" in the database,
        otherwise store "no".
        """
        try :
            if not is_user_registered (ctx .author .id ):
                embed =Embed (
                title ="**Registration Required**",
                description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 

            if not is_user_premium (ctx .author .id ):
                embed =Embed (
                title ="**Upgrade to Lumen Premium**",
                description ="This command is only available to premium users. Consider upgrading to Lumen Premium.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 

            store_value ="yes"if arg .lower ()=="on"else "no"

            try :
                conn =get_database_connection ()
            except Exception as e :
                embed =Embed (
                title ="Error",
                description =f"Could not establish a database connection. ({e })",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 

            try :
                cursor =conn .cursor ()
                user_id =str (ctx .author .id )

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
                await ctx .send (embed =embed ,delete_after =10 )
                return 
            finally :
                conn .close ()

            embed =Embed (
            title ="Success",
            description =f"Your button state has been stored as **{store_value }**.",
            color =0x000001 
            )
            await ctx .send (embed =embed )
        except Exception as e :

            embed =Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =0xff0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )

    @storebutton .error 
    async def storebutton_error (self ,ctx ,error ):
        """
        Error handler for the storebutton command to catch missing arguments.
        """
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =Embed (
            title ="Missing Arguments",
            description ="Missing required argument. Usage: +storebutton <on>",
            color =0xff0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
        else :
            raise error 

async def setup (bot :commands .Bot ):
    await bot .add_cog (PreStoreButton (bot ))
