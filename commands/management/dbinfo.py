import discord 
from discord .ext import commands 
import sqlite3 
import os 
import time 
import psutil 
import platform 
from config import BOT_INFO_PASSWORD ,DEV_CHAMBER_ROLE 
from discord .ui import Button ,View ,Modal ,TextInput 
import asyncio 

password =BOT_INFO_PASSWORD 


def check_db_speed (db_path ):
    start_time =time .time ()
    try :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT name FROM sqlite_master WHERE type='table';")
        tables =cursor .fetchall ()
        conn .close ()
    except Exception as e :
        return {
        "name":os .path .basename (db_path ),
        "speed":None ,
        "tables":0 ,
        "status":f"Error: {str (e )}"
        }
    end_time =time .time ()
    return {
    "name":os .path .basename (db_path ),
    "speed":round (end_time -start_time ,4 ),
    "tables":len (tables ),
    "status":"OK"
    }


def get_databases_in_directory (directory ):
    if not os .path .isdir (directory ):
        return None 
    return [os .path .join (directory ,file )for file in os .listdir (directory )if file .endswith (".db")]

class PasswordModal (Modal ):
    def __init__ (self ,directory ):
        super ().__init__ (title ="Password Entry")
        self .directory =directory 
        self .password_input =TextInput (
        label ="Password",
        style =discord .TextStyle .short ,
        placeholder ="Enter the password",
        required =True ,
        )
        self .add_item (self .password_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        if self .password_input .value ==password :
            databases =get_databases_in_directory (self .directory )
            if not databases :
                await interaction .response .send_message (f"No SQLite databases found in `{self .directory }`.",ephemeral =True )
                return 

            db_details =[]
            for db in databases :
                details =check_db_speed (db )
                db_details .append (details )

            embed =create_dbinfo_embed (self .directory ,db_details )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        else :
            await interaction .response .send_message ("Incorrect password.",ephemeral =True )

class DBInfoView (View ):
    def __init__ (self ,directory ):
        super ().__init__ ()
        self .directory =directory 

    @discord .ui .button (label ="ENTER PASSWORD",style =discord .ButtonStyle .success )
    async def enter_password (self ,interaction :discord .Interaction ,button :Button ):
        await interaction .response .send_modal (PasswordModal (self .directory ))

    @discord .ui .button (label ="CANCEL",style =discord .ButtonStyle .red )
    async def cancel (self ,interaction :discord .Interaction ,button :Button ):
        await interaction .message .delete ()


def create_dbinfo_embed (directory ,db_details ):
    embed =discord .Embed (
    title =f"Database Information for `{directory }`",
    description ="Detailed status of all SQLite databases in the specified directory.",
    color =discord .Color .from_str ("#2f3136")
    )

    total_databases =len (db_details )
    embed .add_field (name ="Total Databases",value =f"`{total_databases }`",inline =False )

    for db in db_details :
        speed =f"`{db ['speed']}s`"if db ['speed']is not None else "`N/A`"
        status =f"`{db ['status']}`"
        tables =f"`{db ['tables']}`"

        embed .add_field (
        name =db ['name'],
        value =(
        f"Connection Speed: {speed }\n"
        f"Number of Tables: {tables }\n"
        f"Status: {status }"
        ),
        inline =False 
        )

    return embed 

class DBInfo (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def dbinfo (self ,ctx ,directory :str ):

        if not any (role .id ==DEV_CHAMBER_ROLE for role in ctx .author .roles ):
            error_embed =discord .Embed (
            title ="Permission Denied",
            description ="You do not have the required permissions to run this command.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed ,delete_after =5 )
            await ctx .message .delete ()
            return 


        if not os .path .isdir (directory ):
            error_embed =discord .Embed (
            title ="Directory Not Found",
            description =f"The directory `{directory }` does not exist.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed ,delete_after =5 )
            await ctx .message .delete ()
            return 


        embed =discord .Embed (
        title ="Database Information (Admin Only)",
        description ="Please click 'ENTER PASSWORD' to proceed.",
        color =discord .Color .from_str ("#2f3136")
        )
        view =DBInfoView (directory )
        await ctx .send (embed =embed ,view =view )
        await ctx .message .delete ()

async def setup (bot ):
    await bot .add_cog (DBInfo (bot ))