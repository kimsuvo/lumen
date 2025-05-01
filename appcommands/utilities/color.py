import os 
import re 
import sqlite3 
import discord 
from discord import Embed 
from discord .ext import commands 
from discord import app_commands 


from functions .color_functions import db_utils 

CREDENTIALS_DATABASE_DIR ="credentialsdatabase"

def is_user_registered (user_id ):
    for db_file in os .listdir (CREDENTIALS_DATABASE_DIR ):
        if db_file .endswith (".db"):
            db_path =os .path .join (CREDENTIALS_DATABASE_DIR ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
    return False 

def is_user_premium (user_id :int )->bool :
    premium_db_dir ="premiumdatabase"
    from glob import glob 
    db_files =sorted (glob (os .path .join (premium_db_dir ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM premium WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 

class Color (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 
        self .database_dir =db_utils .DATABASE_DIR 
        if not os .path .exists (self .database_dir ):
            os .makedirs (self .database_dir )
        self .predefined_colors ={
        "red":"#ff0000",
        "green":"#00ff00",
        "yellow":"#ffff00",
        "blue":"#0000ff",
        "white":"#ffffff",
        "black":"#000001"
        }


    color =app_commands .Group (name ="color",description ="Color related commands")

    @color .command (name ="preset",description ="Set your color using predefined choices")
    @app_commands .describe (color_choice ="Choose one of the available colors")
    @app_commands .choices (color_choice =[
    app_commands .Choice (name ="red",value ="red"),
    app_commands .Choice (name ="green",value ="green"),
    app_commands .Choice (name ="yellow",value ="yellow"),
    app_commands .Choice (name ="blue",value ="blue"),
    app_commands .Choice (name ="white",value ="white"),
    app_commands .Choice (name ="black",value ="black")
    ])
    async def preset (self ,interaction :discord .Interaction ,color_choice :app_commands .Choice [str ]):
        user_id =str (interaction .user .id )

        if not is_user_registered (interaction .user .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        color_hex =self .predefined_colors [color_choice .value ]
        conn =None 
        try :

            user_db =db_utils .find_user_db (user_id )
            if user_db :
                conn =sqlite3 .connect (user_db )
                c =conn .cursor ()
                c .execute ("SELECT colorlock FROM colors WHERE user_id=?",(user_id ,))
                result =c .fetchone ()
                if result and result [0 ].lower ()=="yes":
                    embed =Embed (
                    title ="Color Locked",
                    description ="Your color is locked and cannot be changed.",
                    color =discord .Color .red ()
                    )
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                    return 
                c .execute ("UPDATE colors SET color=? WHERE user_id=?",(color_hex ,user_id ))
                conn .commit ()
                embed =Embed (
                title ="Success",
                description =f"Your color has been updated to {color_hex }.",
                color =0x000001 
                )
                await interaction .response .send_message (embed =embed )
            else :

                active_db =db_utils .get_active_db ()
                conn =sqlite3 .connect (active_db )
                c =conn .cursor ()
                c .execute ("INSERT INTO colors (user_id, color, colorlock) VALUES (?, ?, ?)",
                (user_id ,color_hex ,"no"))
                conn .commit ()
                embed =Embed (
                title ="Success",
                description =f"Your color has been set to {color_hex }.",
                color =0x000001 
                )
                await interaction .response .send_message (embed =embed )
        except sqlite3 .Error as e :
            embed =Embed (
            title ="Database Error",
            description =f"An error occurred while accessing the database: {e }",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        except Exception as e :
            embed =Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        finally :
            if conn :
                try :
                    conn .close ()
                except Exception as e :
                    print (f"Error closing database connection: {e }")

    @color .command (name ="custom",description ="Set a custom hex color (Premium users only)")
    @app_commands .describe (hex_code ="Enter a valid hex code (e.g., #ff0000)")
    async def custom (self ,interaction :discord .Interaction ,hex_code :str ):
        user_id =str (interaction .user .id )

        if not is_user_registered (interaction .user .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not is_user_premium (interaction .user .id ):
            embed =Embed (
            title ="**Upgrade to Lumen Premium**",
            description =("Custom colors are available only to premium users. "
            "Consider upgrading to Lumen Premium."),
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not re .fullmatch (r'^#[0-9a-fA-F]{6}$',hex_code ):
            embed =Embed (
            title ="Error",
            description ="Invalid color format! Please use a valid hex code (e.g., `#ff0000`).",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        color_hex =hex_code 
        conn =None 
        try :
            user_db =db_utils .find_user_db (user_id )
            if user_db :
                conn =sqlite3 .connect (user_db )
                c =conn .cursor ()
                c .execute ("SELECT colorlock FROM colors WHERE user_id=?",(user_id ,))
                result =c .fetchone ()
                if result and result [0 ].lower ()=="yes":
                    embed =Embed (
                    title ="Color Locked",
                    description ="Your color is locked and cannot be changed.",
                    color =discord .Color .red ()
                    )
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                    return 
                c .execute ("UPDATE colors SET color=? WHERE user_id=?",(color_hex ,user_id ))
                conn .commit ()
                embed =Embed (
                title ="Success",
                description =f"Your color has been updated to {color_hex }.",
                color =0x000001 
                )
                await interaction .response .send_message (embed =embed )
            else :
                active_db =db_utils .get_active_db ()
                conn =sqlite3 .connect (active_db )
                c =conn .cursor ()
                c .execute ("INSERT INTO colors (user_id, color, colorlock) VALUES (?, ?, ?)",
                (user_id ,color_hex ,"no"))
                conn .commit ()
                embed =Embed (
                title ="Success",
                description =f"Your color has been set to {color_hex }.",
                color =0x000001 
                )
                await interaction .response .send_message (embed =embed )
        except sqlite3 .Error as e :
            embed =Embed (
            title ="Database Error",
            description =f"An error occurred while accessing the database: {e }",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        except Exception as e :
            embed =Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        finally :
            if conn :
                try :
                    conn .close ()
                except Exception as e :
                    print (f"Error closing database connection: {e }")

async def setup (bot :commands .Bot ):
    await bot .add_cog (Color (bot ))
