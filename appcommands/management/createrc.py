import os 
import sqlite3 
import random 
import string 
import discord 
from discord import app_commands 
from discord .ext import commands 
import config 
from datetime import datetime ,timedelta 
from zoneinfo import ZoneInfo 
import io 


REDEEM_DB_DIR ="redeemcodes"
REDEEM_TABLE ="codes"
MAX_CODES_PER_DB =10000 


os .makedirs (REDEEM_DB_DIR ,exist_ok =True )

def get_redeem_db_path ()->str :
    """
    Selects an existing redeem code database with less than MAX_CODES_PER_DB entries.
    If none is found, creates a new one with the next sequential name.
    """
    files =[f for f in os .listdir (REDEEM_DB_DIR )if f .startswith ("redeem_")and f .endswith (".db")]
    files .sort (key =lambda f :int (f .split ("_")[1 ].split (".")[0 ])if f .split ("_")[1 ].split (".")[0 ].isdigit ()else 0 )
    for filename in files :
        db_path =os .path .join (REDEEM_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {REDEEM_TABLE } (
                redeem_code TEXT PRIMARY KEY,
                duration INTEGER
            )
        """)
        conn .commit ()
        c .execute (f"SELECT COUNT(*) FROM {REDEEM_TABLE }")
        count =c .fetchone ()[0 ]
        conn .close ()
        if count <MAX_CODES_PER_DB :
            return db_path 


    next_number =1 
    if files :
        try :
            next_number =int (files [-1 ].split ("_")[1 ].split (".")[0 ])+1 
        except ValueError :
            next_number =1 
    new_db_name =f"redeem_{next_number }.db"
    new_db_path =os .path .join (REDEEM_DB_DIR ,new_db_name )
    conn =sqlite3 .connect (new_db_path )
    c =conn .cursor ()
    c .execute (f"""
        CREATE TABLE IF NOT EXISTS {REDEEM_TABLE } (
            redeem_code TEXT PRIMARY KEY,
            duration INTEGER
        )
    """)
    conn .commit ()
    conn .close ()
    return new_db_path 

def code_exists (redeem_code :str )->bool :
    """
    Checks all databases in REDEEM_DB_DIR to see if the redeem code already exists.
    """
    for filename in os .listdir (REDEEM_DB_DIR ):
        if not filename .startswith ("redeem_")or not filename .endswith (".db"):
            continue 
        db_path =os .path .join (REDEEM_DB_DIR ,filename )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()
        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {REDEEM_TABLE } (
                redeem_code TEXT PRIMARY KEY,
                duration INTEGER
            )
        """)
        c .execute (f"SELECT 1 FROM {REDEEM_TABLE } WHERE redeem_code = ?",(redeem_code ,))
        result =c .fetchone ()
        conn .close ()
        if result :
            return True 
    return False 

def generate_redeem_code ()->str :
    """
    Generates a 20-character redeem code formatted as:
    XXXXX-XXXXX-XXXXX-XXXXX,
    where each X is a capital letter or digit.
    """
    groups =[]
    for _ in range (4 ):
        group =''.join (random .choices (string .ascii_uppercase +string .digits ,k =5 ))
        groups .append (group )
    return '-'.join (groups )

class CreateRCCog (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @app_commands .command (
    name ="createrc",
    description ="Create redeem codes with a set duration (days) and a specified amount (1-100)."
    )
    @app_commands .describe (
    options ="Duration in days",
    amount ="Number of codes to generate (between 1 and 100)"
    )
    @app_commands .choices (options =[
    app_commands .Choice (name ="7 days",value =7 ),
    app_commands .Choice (name ="30 days",value =30 ),
    app_commands .Choice (name ="90 days",value =90 ),
    app_commands .Choice (name ="180 days",value =180 ),
    app_commands .Choice (name ="365 days",value =365 )
    ])

    @app_commands .guilds (discord .Object (id =config .DEV_CHAMBER_GUILD_ID ))
    async def createrc (
    self ,
    interaction :discord .Interaction ,
    options :app_commands .Choice [int ],
    amount :app_commands .Range [int ,1 ,100 ]
    ):
        duration_option =options .value 


        management_role_id =config .DEV_CHAMBER_ROLE 
        if management_role_id not in [role .id for role in interaction .user .roles ]:
            await interaction .response .send_message (
            "You do not have permission to run this command.",
            ephemeral =True 
            )
            return 

        codes_generated =[]
        db_path =get_redeem_db_path ()
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()

        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {REDEEM_TABLE } (
                redeem_code TEXT PRIMARY KEY,
                duration INTEGER
            )
        """)
        conn .commit ()


        for _ in range (amount ):
            redeem_code =generate_redeem_code ()

            while code_exists (redeem_code ):
                redeem_code =generate_redeem_code ()
            try :
                c .execute (
                f"INSERT INTO {REDEEM_TABLE } (redeem_code, duration) VALUES (?, ?)",
                (redeem_code ,duration_option )
                )
                codes_generated .append (redeem_code )
            except sqlite3 .IntegrityError :

                continue 

        conn .commit ()
        conn .close ()

        if codes_generated :

            file_content ="\n".join (codes_generated )
            file_buffer =io .BytesIO (file_content .encode ('utf-8'))
            redeem_file =discord .File (fp =file_buffer ,filename ="redeem_codes.txt")


            ist_now =datetime .now (ZoneInfo ("Asia/Kolkata"))
            embed =discord .Embed (
            title ="Lumen Premium Redeem Codes Generated",
            color =0x000001 ,
            timestamp =ist_now 
            )
            embed .add_field (name ="Timestamp IST",value =ist_now .strftime ("%Y-%m-%d %H:%M:%S"),inline =False )
            embed .add_field (name ="Number of Redeem Codes",value =str (len (codes_generated )),inline =False )
            embed .add_field (name ="Days",value =str (duration_option ),inline =False )
            embed .add_field (name ="Generated By",value =interaction .user .name ,inline =False )

            await interaction .response .send_message (embed =embed ,file =redeem_file )
        else :
            await interaction .response .send_message (
            "Error creating redeem codes. Please try again.",
            ephemeral =True 
            )

async def setup (bot :commands .Bot ):
    await bot .add_cog (CreateRCCog (bot ))
