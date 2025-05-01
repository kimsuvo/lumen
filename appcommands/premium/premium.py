

import discord 
from discord import app_commands 
from discord .ext import commands 
import sqlite3 
from datetime import datetime ,timedelta 
from zoneinfo import ZoneInfo 
import os 
import re 
import config 


from functions .premium_functions .premium_activate import (
is_user_registered ,
find_and_consume_redeem_code ,
user_has_premium ,
get_user_premium_db ,
get_premium_db_path ,
update_or_insert_image ,
update_badges ,
verify_gumroad_license ,
is_redeem_code_in_global ,
is_redeem_code_in_user_db 
)

class PremiumCog (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @app_commands .command (name ="premium",description ="Activate or extend premium with your redeem code.")
    async def premium (self ,interaction :discord .Interaction ,redeem_code :str ):

        await interaction .response .defer (ephemeral =True )
        user_id =str (interaction .user .id )


        if not is_user_registered (user_id ):
            await interaction .followup .send ("You must be registered with Lumen to use this command.")
            return 


        duration =find_and_consume_redeem_code (redeem_code )
        if duration is None :

            duration =verify_gumroad_license (redeem_code )
            if duration is None :
                await interaction .followup .send ("Invalid or already used redeem code.")
                return 


        if is_redeem_code_in_global (redeem_code )or (user_has_premium (user_id )and is_redeem_code_in_user_db (user_id ,redeem_code )):
            await interaction .followup .send ("This redeem code has already been activated and cannot be reused.")
            return 



        now =datetime .now (ZoneInfo ("Asia/Kolkata"))

        if user_has_premium (user_id ):

            premium_db_path =get_user_premium_db (user_id )
            conn =sqlite3 .connect (premium_db_path )
            c =conn .cursor ()
            c .execute ("""   
                CREATE TABLE IF NOT EXISTS premium (
                    user_id TEXT PRIMARY KEY,
                    redeem_code TEXT,
                    duration INTEGER,
                    start_date TEXT,
                    expiry_date TEXT
                )
            """)
            conn .commit ()
            c .execute ("SELECT expiry_date, duration, start_date FROM premium WHERE user_id = ?",(user_id ,))
            row =c .fetchone ()
            if row :
                current_expiry_str ,current_duration ,current_start_str =row 
                try :
                    current_expiry =datetime .fromisoformat (current_expiry_str )
                except Exception :
                    current_expiry =now 

                base_date =current_expiry if current_expiry >now else now 
                new_expiry =base_date +timedelta (days =duration )
                new_duration =current_duration +duration 
                c .execute ("""
                    UPDATE premium
                    SET redeem_code = ?, duration = ?, expiry_date = ?
                    WHERE user_id = ?
                """,(redeem_code ,new_duration ,new_expiry .isoformat (),user_id ))
                conn .commit ()
                conn .close ()
                premium_status ="extended"
                start_date =datetime .fromisoformat (current_start_str )
            else :
                conn .close ()
                await interaction .followup .send ("Unexpected error: premium record not found.")
                return 
        else :

            start_date =now 
            new_expiry =start_date +timedelta (days =duration )
            start_date_str =start_date .isoformat ()
            expiry_date_str =new_expiry .isoformat ()
            premium_db_path =get_premium_db_path ()
            conn =sqlite3 .connect (premium_db_path )
            c =conn .cursor ()
            c .execute ("""
                CREATE TABLE IF NOT EXISTS premium (
                    user_id TEXT PRIMARY KEY,
                    redeem_code TEXT,
                    duration INTEGER,
                    start_date TEXT,
                    expiry_date TEXT
                )
            """)
            try :
                c .execute ("""
                    INSERT INTO premium (user_id, redeem_code, duration, start_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?)
                """,(user_id ,redeem_code ,duration ,start_date_str ,expiry_date_str ))
            except sqlite3 .IntegrityError :

                await interaction .followup .send ("You already have premium active!")
                conn .close ()
                return 
            conn .commit ()
            conn .close ()
            premium_status ="activated"


        image_thumbnail_url ="https://media.discordapp.net/attachments/1200750312844165203/1335544847796408410/lumenpremium.png?ex=67a08e90&is=679f3d10&hm=f011cd3b30ec3e6ebcc588cfae48432a70987b3cb40146046d817e8391abd43e&=&format=webp&quality=lossless&width=670&height=670"
        image_banner_url ="https://media.discordapp.net/attachments/1200750312844165203/1335544848266301520/lumenpremiumbanner.png?ex=67a08e91&is=679f3d11&hm=a83ae81ff8f34d2c33fd32246f42fa9251e07f0b1955b7fdd19eec7968ef124f&=&format=webp&quality=lossless&width=611&height=215"
        update_or_insert_image (user_id ,image_thumbnail_url ,image_banner_url )


        update_badges (user_id )

        tick_emoji ="<:premium_verified:1341794427378864208>"
        db_dir ="verifiedusers"
        os .makedirs (db_dir ,exist_ok =True )


        db_files =[]
        for filename in os .listdir (db_dir ):
            match =re .match (r"verified_(\d+)\.db$",filename )
            if match :
                db_files .append ((int (match .group (1 )),filename ))
        db_files .sort (key =lambda x :x [0 ])


        if not db_files :
            db_index =1 
            db_filename =f"verified_{db_index }.db"
            db_path =os .path .join (db_dir ,db_filename )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
            conn .commit ()
            conn .close ()
            db_files .append ((db_index ,db_filename ))


        updated =False 
        for index ,filename in db_files :
            db_path =os .path .join (db_dir ,filename )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
            conn .commit ()
            c .execute ("SELECT * FROM verified WHERE user_id = ?",(user_id ,))
            if c .fetchone ()is not None :

                c .execute ("UPDATE verified SET tick_name = ? WHERE user_id = ?",(tick_emoji ,user_id ))
                conn .commit ()
                conn .close ()
                updated =True 
                break 
            conn .close ()

        if not updated :

            inserted =False 
            for index ,filename in db_files :
                db_path =os .path .join (db_dir ,filename )
                conn =sqlite3 .connect (db_path )
                c =conn .cursor ()
                c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
                conn .commit ()
                c .execute ("SELECT COUNT(*) FROM verified")
                count =c .fetchone ()[0 ]
                if count <20000 :
                    c .execute ("INSERT INTO verified (user_id, tick_name) VALUES (?, ?)",(user_id ,tick_emoji ))
                    conn .commit ()
                    conn .close ()
                    inserted =True 
                    break 
                conn .close ()


            if not inserted :
                new_index =db_files [-1 ][0 ]+1 
                new_filename =f"verified_{new_index }.db"
                db_path =os .path .join (db_dir ,new_filename )
                conn =sqlite3 .connect (db_path )
                c =conn .cursor ()
                c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
                conn .commit ()
                c .execute ("INSERT INTO verified (user_id, tick_name) VALUES (?, ?)",(user_id ,tick_emoji ))
                conn .commit ()
                conn .close ()




        guild =self .bot .get_guild (config .GUILD_ID )
        if guild :
            member =guild .get_member (interaction .user .id )
            if member :
                role =guild .get_role (config .PREMIUM_MEMBER_ROLE )
                if role :
                    await member .add_roles (role )


        start_ts =int (start_date .timestamp ())
        expiry_ts =int (new_expiry .timestamp ())
        embed =discord .Embed (
        title =f"Premium {premium_status .capitalize ()}!",
        description ="Your premium membership has been successfully "+
        ("extended."if premium_status =="extended"else "activated."),
        color =0x000001 ,
        timestamp =datetime .now (ZoneInfo ("Asia/Kolkata"))
        )
        embed .add_field (name ="Redeem Code",value =f"||{redeem_code }||",inline =False )
        if premium_status =="extended":
            embed .add_field (name ="Extension (days)",value =str (duration ),inline =True )
        else :
            embed .add_field (name ="Duration (days)",value =str (duration ),inline =True )
        embed .add_field (name ="Start Date",value =f"<t:{start_ts }:F>",inline =True )
        embed .add_field (name ="Expiry Date",value =f"<t:{expiry_ts }:F>",inline =True )
        embed .set_thumbnail (url =image_thumbnail_url )


        try :
            await interaction .user .send (embed =embed )
            dm_status ="Premium "+premium_status +" successfully!"
        except discord .Forbidden :
            dm_status ="I could not DM you, but your premium is "+premium_status +"."

        await interaction .followup .send (dm_status )

async def setup (bot :commands .Bot ):
    await bot .add_cog (PremiumCog (bot ))
