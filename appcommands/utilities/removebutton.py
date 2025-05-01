import os 
import sqlite3 
import discord 
from discord import app_commands ,Embed 
from discord .ext import commands 


from functions .custom_button .database_cb1 import (
is_user_premium ,
is_user_registered ,
find_custom_button_entry 
)

class RemoveButton (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 


    remove_group =app_commands .Group (name ="remove",description ="Commands to remove entries.")

    @remove_group .command (name ="button",description ="Remove your custom button entry.")
    async def button (self ,interaction :discord .Interaction ):
        """
        Slash command usage:
          /remove button
        This command removes your existing custom button entry.
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

            user_id =str (interaction .user .id )
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
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                    return 
                except sqlite3 .Error as e :
                    embed =Embed (
                    title ="Error",
                    description =f"Failed to remove your entry: {e }",
                    color =0xff0000 
                    )
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                    return 
            else :
                embed =Embed (
                title ="No Entry Found",
                description ="You don't have a custom button entry to remove.",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 

        except Exception as e :
            embed =Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (RemoveButton (bot ))
