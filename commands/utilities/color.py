
import os 
import re 
import sqlite3 
import discord 
from discord import Embed 
from discord .ext import commands 
from glob import glob 


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

class SetColor (commands .Cog ):
    def __init__ (self ,bot ):
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

    @commands .command (name ="color")
    async def color (self ,ctx ,color_input :str ):

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 

        user_id =str (ctx .author .id )
        premium =is_user_premium (ctx .author .id )

        if not premium :
            color_lower =color_input .lower ()
            if color_lower not in self .predefined_colors :
                embed =discord .Embed (
                title ="**Upgrade to Lumen Premium**",
                description =("You can only use the predefined colors: red, green, yellow, blue, white and black. "
                "Consider upgrading to Lumen Premium for custom colors."),
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 
            color_hex =self .predefined_colors [color_lower ]
        else :
            if not re .fullmatch (r'^#[0-9a-fA-F]{6}$',color_input ):
                embed =discord .Embed (
                title ="Error",
                description ="Invalid color format! Please use a valid hex code (e.g., `#ff0000`).",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 
            color_hex =color_input 


        user_db =db_utils .find_user_db (user_id )
        conn =None 
        try :
            if user_db :
                conn =sqlite3 .connect (user_db )
                c =conn .cursor ()
                c .execute ("SELECT colorlock FROM colors WHERE user_id=?",(user_id ,))
                result =c .fetchone ()
                if result and result [0 ].lower ()=="yes":
                    embed =discord .Embed (
                    title ="Color Locked",
                    description ="Your color is locked and cannot be changed.",
                    color =discord .Color .red ()
                    )
                    await ctx .send (embed =embed )
                    return 
                c .execute ("UPDATE colors SET color=? WHERE user_id=?",(color_hex ,user_id ))
                conn .commit ()
                embed =discord .Embed (
                title ="Success",
                description =f"Your color has been updated to {color_hex }.",
                color =0x000001 
                )
                await ctx .send (embed =embed )
            else :

                active_db =db_utils .get_active_db ()
                conn =sqlite3 .connect (active_db )
                c =conn .cursor ()
                c .execute ("INSERT INTO colors (user_id, color, colorlock) VALUES (?, ?, ?)",
                (user_id ,color_hex ,"no"))
                conn .commit ()
                embed =discord .Embed (
                title ="Success",
                description =f"Your color has been set to {color_hex }.",
                color =0x000001 
                )
                await ctx .send (embed =embed )
        except sqlite3 .Error as e :
            embed =discord .Embed (
            title ="Database Error",
            description =f"An error occurred while accessing the database: {e }",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
        except Exception as e :
            embed =discord .Embed (
            title ="Unexpected Error",
            description =f"An unexpected error occurred: {e }",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
        finally :
            if conn :
                try :
                    conn .close ()
                except Exception as e :
                    print (f"Error closing database connection: {e }")

    @color .error 
    async def color_error (self ,ctx ,error ):
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="Invalid Arguments",
            description =("You must specify a color. For premium users, use a valid hex code (e.g., `#ff0000`), "
            "and for non-premium users, use one of the following: red, green, yellow, blue, white, black."),
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
        else :
            raise error 

async def setup (bot ):
    await bot .add_cog (SetColor (bot ))
