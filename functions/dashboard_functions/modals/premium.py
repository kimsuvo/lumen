

import discord 
from discord .ui import Modal ,TextInput 
from discord import TextStyle 
import sqlite3 
from datetime import datetime ,timedelta 
from zoneinfo import ZoneInfo 
import config 
from functions .premium_functions .premium_activate import (
is_user_registered ,
find_and_consume_redeem_code ,
user_has_premium ,
get_user_premium_db ,
get_premium_db_path ,
update_or_insert_image ,
update_badges ,
)
from functions .dashboard_functions .accounts .setrecovery import fetch_recovery_email 
from functions .dashboard_functions .accounts .premium import fetch_dashboard_premium 



class PremiumModal (Modal ,title ="Activate/Extend Premium"):
    redeem_input =TextInput (
    label ="Enter Redeem Code:",
    style =TextStyle .short ,
    placeholder ="Type your redeem code here...",
    required =True ,
    max_length =50 
    )

    def __init__ (self ,user_id :int ):
        super ().__init__ ()

        self .user_id =str (user_id )

    async def on_submit (self ,interaction :discord .Interaction ):
        redeem_code =self .redeem_input .value .strip ()
        now =datetime .now (ZoneInfo ("Asia/Kolkata"))


        if not is_user_registered (self .user_id ):
            await interaction .response .send_message ("You must be registered with Lumen to activate premium.",ephemeral =True )
            return 


        duration =find_and_consume_redeem_code (redeem_code )
        if duration is None :
            await interaction .response .send_message ("Invalid or already used redeem code.",ephemeral =True )
            return 


        if user_has_premium (self .user_id ):

            premium_db_path =get_user_premium_db (self .user_id )
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
            c .execute ("SELECT expiry_date, duration, start_date FROM premium WHERE user_id = ?",(self .user_id ,))
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
                """,(redeem_code ,new_duration ,new_expiry .isoformat (),self .user_id ))
                conn .commit ()
                conn .close ()
                premium_status ="extended"
                start_date =datetime .fromisoformat (current_start_str )
            else :
                conn .close ()
                await interaction .response .send_message ("Unexpected error: premium record not found.",ephemeral =True )
                return 
        else :

            start_date =now 
            new_expiry =start_date +timedelta (days =duration )
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
                """,(self .user_id ,redeem_code ,duration ,start_date .isoformat (),new_expiry .isoformat ()))
            except sqlite3 .IntegrityError :
                await interaction .response .send_message ("You already have premium active!",ephemeral =True )
                conn .close ()
                return 
            conn .commit ()
            conn .close ()
            premium_status ="activated"


        image_thumbnail_url ="https://media.discordapp.net/attachments/1200750312844165203/1335544847796408410/lumenpremium.png?ex=67a08e90&is=679f3d10&hm=f011cd3b30ec3e6ebcc588cfae48432a70987b3cb40146046d817e8391abd43e&=&format=webp&quality=lossless&width=670&height=670"
        image_banner_url ="https://media.discordapp.net/attachments/1200750312844165203/1335544848266301520/lumenpremiumbanner.png?ex=67a08e91&is=679f3d11&hm=a83ae81ff8f34d2c33fd32246f42fa9251e07f0b1955b7fdd19eec7968ef124f&=&format=webp&quality=lossless&width=611&height=215"
        update_or_insert_image (self .user_id ,image_thumbnail_url ,image_banner_url )
        update_badges (self .user_id )


        guild =interaction .guild 
        if guild :
            member =guild .get_member (int (self .user_id ))
            if member :
                role =guild .get_role (config .PREMIUM_MEMBER_ROLE )
                if role :
                    await member .add_roles (role )


        start_ts =int (start_date .timestamp ())
        expiry_ts =int (new_expiry .timestamp ())
        embed =discord .Embed (
        title =f"Premium {premium_status .capitalize ()}!",
        description ="Your premium membership has been successfully "+("extended."if premium_status =="extended"else "activated."),
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
        except discord .Forbidden :

            await interaction .response .send_message ("Could not send DM. Please check your DM settings.",ephemeral =True )
            return 

        from commands .utilities .dashboard import AccountSettingsView 


        recovery_status =fetch_recovery_email (interaction .user .id )
        premium_status =fetch_dashboard_premium (interaction .user .id )

        account_embed =discord .Embed (
        title ="Account Settings",
        description ="Your current account details.",
        color =0x000001 
        )
        account_embed .add_field (name ="Recovery Email:",value =f"-# {recovery_status }",inline =False )


        from functions .dwc .db_utils import is_user_dwc 
        dwc_active =is_user_dwc (str (interaction .user .id ))
        dwc_status ="Active"if dwc_active else "Inactive"
        account_embed .add_field (name ="DWC Status:",value =f"-# {dwc_status }",inline =False )


        from functions .blacklist .db_utils import find_user_blacklist_db 
        conn ,cursor =find_user_blacklist_db (str (interaction .user .id ))
        if conn and cursor :
            cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(str (interaction .user .id ),))
            result =cursor .fetchone ()
            blacklist_status =result [0 ]if result else "Not Blacklisted"
            conn .close ()
        else :
            blacklist_status ="Not Blacklisted"
        account_embed .add_field (name ="Blacklist Status:",value =f"{blacklist_status }",inline =False )


        from functions .warnings .db_utils import DatabaseManager 
        warnings_manager =DatabaseManager (db_dir ="warningsdatabase",db_prefix ="warnings_")
        warnings_list =warnings_manager .get_warnings_for_user (str (interaction .user .id ))
        warnings_status =f"{len (warnings_list )} Warning(s)"if warnings_list else "No Warnings"
        account_embed .add_field (name ="Warnings:",value =f"{warnings_status }",inline =False )

        account_embed .add_field (name ="Premium Status:",value =f"-# {premium_status }",inline =False )
        account_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")


        await interaction .response .edit_message (embed =account_embed ,view =AccountSettingsView (recovery_email =recovery_status ,user_id =interaction .user .id ))