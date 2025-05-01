import os 
import sqlite3 
import discord 
from discord import app_commands ,Embed 
from discord .ext import commands 


from functions .custom_button .database_cb1 import (
is_user_premium ,
is_user_registered ,
get_database_connection 
)

class CustomButton (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @app_commands .command (
    name ="button",
    description ="Set or update your custom button with a name and URL."
    )
    @app_commands .describe (
    name ="The name of your button.",
    url ="The URL of your button."
    )
    async def button (self ,interaction :discord .Interaction ,name :str ,url :str ):
        """
        Slash command usage:
          /button <name> <url>
        This command sets or updates your custom button.
        """
        try :

            if not is_user_registered (interaction .user .id ):
                embed =Embed (
                title ="**Registration Required**",
                description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 

            if not is_user_premium (interaction .user .id ):
                embed =Embed (
                title ="**Upgrade to Lumen Premium**",
                description ="This command is only available to premium users. Consider upgrading to Lumen Premium.",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 


            if not name or name .strip ()==""or not url or url .strip ()=="":
                embed =Embed (
                title ="Invalid Format",
                description ="Please provide both <name> and <url> when setting your custom button.\nUsage: /button <name> <url>",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 

            user_id =str (interaction .user .id )


            button_name =name .strip ()
            if len (button_name )>70 :
                embed =Embed (
                title ="Error",
                description ="The button name cannot exceed 70 characters.",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 


            url =url .strip ()
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
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 

            try :
                cursor =conn .cursor ()

                try :
                    cursor .execute (
                    "INSERT INTO custombuttons (user_id, button_name, url) VALUES (?, ?, ?)",
                    (user_id ,button_name ,url )
                    )
                except sqlite3 .IntegrityError :
                    cursor .execute (
                    "UPDATE custombuttons SET button_name = ?, url = ? WHERE user_id = ?",
                    (button_name ,url ,user_id )
                    )
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
            description =f"Your custom button has been stored as:\n**Name:** {button_name }\n**URL:** {url }",
            color =0x000001 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

        except Exception as e :
            embed =Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (CustomButton (bot ))
