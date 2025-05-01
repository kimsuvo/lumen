import os 
import sqlite3 
import discord 
from discord .ext import commands 
from discord import Embed 


from functions .custom_button .database_cb1 import (
is_user_premium ,
is_user_registered ,
find_custom_button_entry ,
get_database_connection 
)

class PreCustomButton (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def button (self ,ctx ,*,arg :str =None ):
        """
        Command usage:
          +button <name>, <url>
        If no arguments are provided (i.e. the command is used as +button), the user's entry is removed.
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

            user_id =str (ctx .author .id )


            if arg is None or not arg .strip ():
                db_directory ="custombuttondatabase"
                existing_db_file =find_custom_button_entry (user_id ,db_directory )
                if existing_db_file :
                    try :
                        conn =sqlite3 .connect (existing_db_file )
                        cursor =conn .cursor ()
                        cursor .execute ("DELETE FROM custombuttons WHERE user_id = ?",(user_id ,))
                        conn .commit ()
                        conn .close ()
                        embed =Embed (
                        title ="Success",
                        description ="Your custom button entry has been removed.",
                        color =0x000001 
                        )
                        await ctx .send (embed =embed )
                        return 
                    except sqlite3 .Error as e :
                        embed =Embed (
                        title ="Error",
                        description =f"Failed to remove your entry: {e }",
                        color =0xff0000 
                        )
                        await ctx .send (embed =embed ,delete_after =10 )
                        return 
                else :
                    embed =Embed (
                    title ="Invalid Arguments",
                    description ="Usage: +button <name>, <url>",
                    color =0xff0000 
                    )
                    await ctx .send (embed =embed ,delete_after =10 )
                    return 


            parts =arg .split (",",1 )
            if len (parts )!=2 :
                embed =Embed (
                title ="Invalid Format",
                description ="Usage: +button <name>, <url>",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 

            button_name =parts [0 ].strip ()
            url =parts [1 ].strip ()


            if len (button_name )>70 :
                embed =Embed (
                title ="Error",
                description ="The button name cannot exceed 70 characters.",
                color =0xff0000 
                )
                await ctx .send (embed =embed ,delete_after =10 )
                return 


            if not (url .startswith ("http://")or url .startswith ("https://")):
                url ="https://"+url 


            try :
                conn =get_database_connection (user_id )
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

                try :
                    cursor .execute ("INSERT INTO custombuttons (user_id, button_name, url) VALUES (?, ?, ?)",
                    (user_id ,button_name ,url ))
                except sqlite3 .IntegrityError :
                    cursor .execute ("UPDATE custombuttons SET button_name = ?, url = ? WHERE user_id = ?",
                    (button_name ,url ,user_id ))
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
            description =f"Your custom button has been stored as:\n**Name:** {button_name }\n**URL:** {url }",
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

    @button .error 
    async def button_error (self ,ctx ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =Embed (
            title ="Missing Arguments",
            description ="Missing required argument. Usage: +button <name>, <url>",
            color =0xff0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
        else :
            raise error 

async def setup (bot :commands .Bot ):
    await bot .add_cog (PreCustomButton (bot ))
