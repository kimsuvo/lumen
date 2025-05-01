import discord 
from discord .ext import commands ,tasks 
import os 
import asyncio 
import sqlite3 
from datetime import datetime ,timedelta 
from zoneinfo import ZoneInfo 
from glob import glob 
import pytz 
from commands .management .recoverypanel import RecoveryView 
from functions .pdf_txt_generation_functions .pdf_functions import create_password_protected_pdf 
from functions .pdf_txt_generation_functions .feedback_functions import fetch_feedback_data 


import pandas as pd 
from fpdf import FPDF 
from PyPDF2 import PdfReader ,PdfWriter 

from config import DEV_CHAMBER_GUILD_ID ,BOT_TOKEN ,GUILD_ID ,PREMIUM_MEMBER_ROLE 




REDEEM_DB_DIR ="redeemcodes"
PREMIUM_DB_DIR ="premiumdatabase"
BADGES_DB_DIR ="badgesdatabase"
IMAGEDB_DIR ="imagedatabase"
CREDENTIALS_DB_DIR ="credentialsdatabase"
COLOR_DB_DIR ="colordatabase"
PREMIUM_TABLE ="premium"
REDEEM_TABLE ="codes"
MAX_USERS_PER_DB =10000 
BADGE_TO_REMOVE ="<:lumen_premium_badge:1335561446284857445>"


os .makedirs (REDEEM_DB_DIR ,exist_ok =True )
os .makedirs (PREMIUM_DB_DIR ,exist_ok =True )
os .makedirs (BADGES_DB_DIR ,exist_ok =True )
os .makedirs (IMAGEDB_DIR ,exist_ok =True )
os .makedirs (CREDENTIALS_DB_DIR ,exist_ok =True )
os .makedirs (COLOR_DB_DIR ,exist_ok =True )




intents =discord .Intents .all ()
bot =commands .AutoShardedBot (command_prefix ="+",intents =intents ,help_command =None )

class PremiumView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )


        self .add_item (discord .ui .Button (
        label ="Get Lumen Premium",
        style =discord .ButtonStyle .link ,
        url ="https://lumen.dezinare.com"
        ))


        self .add_item (discord .ui .Button (
        label ="Lumen Support Server",
        style =discord .ButtonStyle .link ,
        url ="https://discord.gg/lumenreport"
        ))

class PremiumReminderView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )

        self .add_item (discord .ui .Button (
        label ="Renew Premium",
        style =discord .ButtonStyle .link ,
        url ="https://lumen.dezinare.com"
        ))





async def load_commands ():
    directories =[
    "appcommands/management",
    "appcommands/premium",
    "appcommands/utilities",
    "commands/feedback",
    "commands/management",
    "commands/utilities",
    "commands/reportstaff",
    "commands/feedbackstaff"
    ]
    for directory in directories :
        path =f"./{directory }"
        if os .path .exists (path ):
            all_files =[f for f in os .listdir (path )if f .endswith (".py")and f !="__init__.py"]
            if not all_files :
                print (f"No files to load in {directory }.")
                continue 

            failed_files =[]

            for filename in all_files :
                try :

                    await bot .load_extension (f"{directory .replace ('/','.')}.{filename [:-3 ]}")
                except commands .ExtensionAlreadyLoaded :
                    await bot .reload_extension (f"{directory .replace ('/','.')}.{filename [:-3 ]}")
                except Exception as e :
                    failed_files .append (f"{filename }: {e }")

            if failed_files :
                print (f"Failed to load the following files from {directory }:\n"+"\n".join (failed_files ))
            else :
                print (f"Loaded all files from {directory }.")




@tasks .loop (hours =24 )
async def check_premium_expirations ():
    now =datetime .now (ZoneInfo ("Asia/Kolkata"))
    print ("Running premium expiration check at",now .isoformat ())


    expired_users =set ()


    premium_files =[f for f in os .listdir (PREMIUM_DB_DIR )if f .startswith ("premium_")and f .endswith (".db")]
    for premium_file in premium_files :
        db_path =os .path .join (PREMIUM_DB_DIR ,premium_file )
        conn =sqlite3 .connect (db_path )
        c =conn .cursor ()

        c .execute (f"""
            CREATE TABLE IF NOT EXISTS {PREMIUM_TABLE } (
                user_id TEXT PRIMARY KEY,
                redeem_code TEXT,
                duration INTEGER,
                start_date TEXT,
                expiry_date TEXT
            )
        """)
        conn .commit ()


        c .execute (f"SELECT user_id, expiry_date FROM {PREMIUM_TABLE }")
        rows =c .fetchall ()
        for row in rows :
            user_id ,expiry_date_str =row 
            try :
                expiry_date =datetime .fromisoformat (expiry_date_str )
            except Exception as e :
                print (f"Error parsing expiry_date for user {user_id }: {e }")
                continue 


            if expiry_date >now and (expiry_date -now )<timedelta (days =1 ):
                try :
                    user =await bot .fetch_user (int (user_id ))
                    embed =discord .Embed (
                    title ="Lumen Premium Expiry Reminder",
                    description ="Your Lumen premium membership is about to expire in less than 24 hours.",
                    color =0x000001 ,
                    )
                    embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")

                    view =PremiumReminderView ()
                    await user .send (embed =embed ,view =view )
                except Exception as e :
                    print (f"Error sending reminder DM to user {user_id }: {e }")
                await asyncio .sleep (0.04 )


            elif expiry_date <=now :
                try :
                    user =await bot .fetch_user (int (user_id ))
                    embed =discord .Embed (
                    title ="Lumen Premium Expired",
                    description =(
                    "Your Lumen premium membership has expired.\n\n"
                    "To continue enjoying premium features, please consider renewing your subscription. "
                    "If you have any questions or need assistance, feel free to reach out on our support server."
                    ),
                    color =0x000001 
                    )
                    embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
                    embed .add_field (name ="Renew Your Premium",value ="[Click here to renew](https://lumen.dezinare.com)",inline =False )
                    embed .add_field (name ="Need Help?",value ="[Join our Support Server](https://discord.gg/lumenreport)",inline =False )
                    embed .set_footer (text ="Lumen Bot")


                    view =PremiumView ()


                    await user .send (embed =embed ,view =view )
                except Exception as e :
                    print (f"Error sending expiration DM to user {user_id }: {e }")

                c .execute (f"DELETE FROM {PREMIUM_TABLE } WHERE user_id = ?",(user_id ,))
                conn .commit ()

                expired_users .add (user_id )
                await asyncio .sleep (0.04 )
        conn .close ()


    for user_id in expired_users :

        guild =bot .get_guild (GUILD_ID )
        if guild :
            member =guild .get_member (int (user_id ))
            if member :
                role =guild .get_role (PREMIUM_MEMBER_ROLE )
                if role in member .roles :
                    try :
                        await member .remove_roles (role )
                        print (f"Removed premium role from user {user_id } in guild {GUILD_ID }.")
                    except Exception as e :
                        print (f"Error removing premium role from user {user_id }: {e }")


        badge_files =[f for f in os .listdir (BADGES_DB_DIR )if f .startswith ("badges_")and f .endswith (".db")]
        for badges_file in badge_files :
            badges_db_path =os .path .join (BADGES_DB_DIR ,badges_file )
            conn_badge =sqlite3 .connect (badges_db_path )
            c_badge =conn_badge .cursor ()
            c_badge .execute ('''
                CREATE TABLE IF NOT EXISTS badges (
                    user_id TEXT PRIMARY KEY,
                    badge_count TEXT
                )
            ''')
            conn_badge .commit ()
            c_badge .execute ("SELECT badge_count FROM badges WHERE user_id = ?",(user_id ,))
            row_badge =c_badge .fetchone ()
            if row_badge :
                current_badges =row_badge [0 ]or ""

                new_badges =current_badges .replace (BADGE_TO_REMOVE ,"").strip ()

                new_badges =" ".join (new_badges .split ())
                if new_badges :
                    c_badge .execute ("UPDATE badges SET badge_count = ? WHERE user_id = ?",(new_badges ,user_id ))
                else :
                    c_badge .execute ("DELETE FROM badges WHERE user_id = ?",(user_id ,))
                conn_badge .commit ()
            conn_badge .close ()


        autofb_db_dir ="autofbdatabase"
        if os .path .exists (autofb_db_dir ):
            autofb_files =[f for f in os .listdir (autofb_db_dir )if f .startswith ("autofb_")and f .endswith (".db")]
            for autofb_file in autofb_files :
                db_path =os .path .join (autofb_db_dir ,autofb_file )
                try :
                    conn_auto =sqlite3 .connect (db_path )
                    c_auto =conn_auto .cursor ()
                    c_auto .execute ("DELETE FROM autofb WHERE user_id = ?",(user_id ,))
                    conn_auto .commit ()
                    print (f"Removed autofb entry for user {user_id } from {autofb_file }.")
                except Exception as e :
                    print (f"Error cleaning autofbdatabase for user {user_id } in {autofb_file }: {e }")
                finally :
                    conn_auto .close ()


        products_db_dir ="productsdatabase"
        if os .path .exists (products_db_dir ):
            prod_files =[f for f in os .listdir (products_db_dir )if f .startswith ("products_")and f .endswith (".db")]
            for prod_file in prod_files :
                db_path =os .path .join (products_db_dir ,prod_file )
                conn_prod =None 
                try :
                    conn_prod =sqlite3 .connect (db_path )
                    c_prod =conn_prod .cursor ()

                    c_prod .execute ("SELECT products, store FROM services_and_products WHERE user_id = ?",(user_id ,))
                    row =c_prod .fetchone ()
                    if row :
                        products_text =row [0 ]or ""
                        store_text =row [1 ]or ""
                        update_fields ={}


                        prod_list =[line .strip ()for line in products_text .splitlines ()if line .strip ()]
                        if len (prod_list )>3 :

                            new_products ="\n".join (prod_list [:3 ])
                            update_fields ["products"]=new_products 


                        if "http://"in store_text or "https://"in store_text :
                            update_fields ["store"]=""


                        if update_fields :

                            set_clause =", ".join ([f"{field } = ?"for field in update_fields .keys ()])
                            params =list (update_fields .values ())
                            params .append (user_id )
                            sql =f"UPDATE services_and_products SET {set_clause } WHERE user_id = ?"
                            c_prod .execute (sql ,params )
                            conn_prod .commit ()

                            update_msgs =[]
                            if "products"in update_fields :
                                update_msgs .append ("kept first 3 products")
                            if "store"in update_fields :
                                update_msgs .append ("emptied store field due to links")
                            print (f"Updated user {user_id } in {prod_file }: {', '.join (update_msgs )}.")
                    else :
                        print (f"No record found for user {user_id } in {prod_file }.")
                except Exception as e :
                    print (f"Error updating productsdatabase for user {user_id } in {prod_file }: {e }")
                finally :
                    if conn_prod :
                        conn_prod .close ()


        image_files =[f for f in os .listdir (IMAGEDB_DIR )if f .startswith ("image_")and f .endswith (".db")]
        for image_file in image_files :
            image_db_path =os .path .join (IMAGEDB_DIR ,image_file )
            try :
                conn_image =sqlite3 .connect (image_db_path )
                c_image =conn_image .cursor ()
                c_image .execute ("DELETE FROM imagethumbnail WHERE user_id = ?",(user_id ,))
                conn_image .commit ()
                print (f"Removed image entry for user {user_id } in {image_file }.")
            except Exception as e :
                print (f"Error updating image database for user {user_id } in {image_file }: {e }")
            finally :
                conn_image .close ()


        credentials_files =[f for f in os .listdir (CREDENTIALS_DB_DIR )if f .startswith ("credentials_")and f .endswith (".db")]
        for cred_file in credentials_files :
            cred_db_path =os .path .join (CREDENTIALS_DB_DIR ,cred_file )
            try :
                conn_cred =sqlite3 .connect (cred_db_path )
                c_cred =conn_cred .cursor ()
                c_cred .execute ("UPDATE users SET recovery_email = '' WHERE user_id = ?",(user_id ,))
                conn_cred .commit ()
                print (f"Cleared recovery email for user {user_id } in {cred_file }.")
            except Exception as e :
                print (f"Error updating credentials database for user {user_id } in {cred_file }: {e }")
            finally :
                conn_cred .close ()


        color_files =[f for f in os .listdir (COLOR_DB_DIR )if f .startswith ("color_")and f .endswith (".db")]
        for color_file in color_files :
            color_db_path =os .path .join (COLOR_DB_DIR ,color_file )
            try :
                conn_color =sqlite3 .connect (color_db_path )
                c_color =conn_color .cursor ()
                c_color .execute ("UPDATE colors SET color = '#000001' WHERE user_id = ?",(user_id ,))
                conn_color .commit ()
                print (f"Reset color for user {user_id } in {color_file }.")
            except Exception as e :
                print (f"Error updating color database for user {user_id } in {color_file }: {e }")
            finally :
                conn_color .close ()



        custom_button_dir ="custombuttondatabase"
        if os .path .exists (custom_button_dir ):
            cb_files =[f for f in os .listdir (custom_button_dir )if f .endswith (".db")]
            for cb_file in cb_files :
                cb_db_path =os .path .join (custom_button_dir ,cb_file )
                try :
                    conn_cb =sqlite3 .connect (cb_db_path )
                    c_cb =conn_cb .cursor ()
                    c_cb .execute ("DELETE FROM custombuttons WHERE user_id = ?",(user_id ,))
                    conn_cb .commit ()
                    print (f"Removed custom button entry for user {user_id } from {cb_file }.")
                except Exception as e :
                    print (f"Error removing custom button entry for user {user_id } from {cb_file }: {e }")
                finally :
                    conn_cb .close ()


        ver_tick_dir ="verifiedusers"
        if os .path .exists (ver_tick_dir ):
            tick_files =[f for f in os .listdir (ver_tick_dir )if f .endswith (".db")]
            for tick_file in tick_files :
                tick_db_path =os .path .join (ver_tick_dir ,tick_file )
                try :
                    conn_cb =sqlite3 .connect (tick_db_path )
                    c_cb =conn_cb .cursor ()
                    c_cb .execute ("DELETE FROM verified WHERE user_id = ?",(user_id ,))
                    conn_cb .commit ()
                    print (f"Removed tick entry for user {user_id } from {tick_file }.")
                except Exception as e :
                    print (f"Error removing tick entry for user {user_id } from {tick_file }: {e }")
                finally :
                    conn_cb .close ()



        store_button_dir ="buttonsdatabase"
        if os .path .exists (store_button_dir ):
            sb_files =[f for f in os .listdir (store_button_dir )if f .endswith (".db")]
            for sb_files in sb_files :
                sb_db_path =os .path .join (store_button_dir ,sb_files )
                try :
                    conn_cb =sqlite3 .connect (sb_db_path )
                    c_cb =conn_cb .cursor ()
                    c_cb .execute ("DELETE FROM buttons WHERE user_id = ?",(user_id ,))
                    conn_cb .commit ()
                    print (f"Removed store button entry for user {user_id } from {cb_file }.")
                except Exception as e :
                    print (f"Error removing store button entry for user {user_id } from {cb_file }: {e }")
                finally :
                    conn_cb .close ()



    print ("Premium expiration check completed.")





class AutoFeedbackLoop (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 
        self .autofb_db_dir ="autofbdatabase"

        os .makedirs (self .autofb_db_dir ,exist_ok =True )
        self .check_feedback_loop .start ()

    def cog_unload (self ):
        self .check_feedback_loop .cancel ()

    def get_autofb_db_files (self ):
        """Return a sorted list of AutoFB database file paths."""
        pattern =os .path .join (self .autofb_db_dir ,"autofb_*.db")
        files =glob (pattern )
        files .sort (key =lambda x :int (os .path .splitext (os .path .basename (x ))[0 ].split ('_')[1 ]))
        return files 

    def fetch_all_autofb_records (self ):
        """
        Fetch all records from all autofb databases.
        Each record is a tuple: (user_id, duration, next_timestamp, db_file).
        """
        records =[]
        for db_file in self .get_autofb_db_files ():
            try :
                conn =sqlite3 .connect (db_file )
                c =conn .cursor ()
                c .execute ("CREATE TABLE IF NOT EXISTS autofb (user_id TEXT PRIMARY KEY, duration INTEGER, next_timestamp TEXT)")
                c .execute ("SELECT user_id, duration, next_timestamp FROM autofb")
                rows =c .fetchall ()
                for row in rows :
                    records .append ((row [0 ],row [1 ],row [2 ],db_file ))
            except sqlite3 .Error as e :
                print (f"Error fetching records from {db_file }: {e }")
            finally :
                conn .close ()
        return records 

    async def send_feedback_pdf (self ,user_id :int ,days :int )->tuple :

        rows =fetch_feedback_data (user_id ,days )
        if not rows :
            return None ,"No feedback found."

        df =pd .DataFrame (
        rows ,columns =['Giver ID','Receiver ID','Feedback','Feedback Type','Timestamp']
        )
        user =self .bot .get_user (int (user_id ))
        username =user .name if user else "Unknown User"
        server_name ="AutoFeedback"
        server_id ="N/A"
        try :
            pdf_path ,_ =create_password_protected_pdf (df ,user_id ,str (days ),username ,server_name ,server_id )
            return pdf_path ,None 
        except Exception as e :
            return None ,str (e )

    @tasks .loop (hours =1 )
    async def check_feedback_loop (self ):
        print ("Running hourly feedback check loop")
        records =self .fetch_all_autofb_records ()

        now =datetime .now (pytz .timezone ("Asia/Kolkata"))
        for record in records :
            user_id ,duration ,next_timestamp_str ,db_file =record 
            try :
                next_timestamp_dt =datetime .fromisoformat (next_timestamp_str )
            except Exception as e :
                print (f"Error parsing timestamp for user {user_id }: {e }")
                continue 

            if now >=next_timestamp_dt :

                user =self .bot .get_user (int (user_id ))
                if not user :
                    print (f"User {user_id } not found or not cached.")
                    continue 

                print (f"Sending scheduled feedback PDF to user {user_id }")
                pdf_path ,error =await self .send_feedback_pdf (user_id ,duration )
                if error :
                    print (f"Error generating PDF for user {user_id }: {error }")
                elif pdf_path :
                    try :
                        dm_channel =await user .create_dm ()
                        embed =discord .Embed (
                        title =f"**__Your Auto Feedback Mail for {duration } Days__**",
                        description ="Attached is your **password-protected** PDF report.\n\n"
                        "**Password Format**:\n"
                        "It's simply your `User ID` + the requested days.\n\n"
                        f"**Example**: If User ID is `102938473628372638` and days = `20`, "
                        f"password = `10293847362837263820`",
                        color =0x000001 
                        )
                        await dm_channel .send (embed =embed ,file =discord .File (pdf_path ))
                        if os .path .exists (pdf_path ):
                            os .remove (pdf_path )


                        await asyncio .sleep (0.04 )


                        new_next_time =now +timedelta (days =duration )
                        new_next_timestamp =new_next_time .isoformat ()
                        try :
                            conn =sqlite3 .connect (db_file )
                            c =conn .cursor ()
                            c .execute ("UPDATE autofb SET next_timestamp = ? WHERE user_id = ?",(new_next_timestamp ,user_id ))
                            conn .commit ()
                        except sqlite3 .Error as e :
                            print (f"Error updating next_timestamp for user {user_id } in {db_file }: {e }")
                        finally :
                            conn .close ()
                    except discord .Forbidden :
                        print (f"Unable to DM user {user_id } (Forbidden).")
                    except Exception as e :
                        print (f"Unexpected error sending DM to user {user_id }: {e }")

        print ("Hourly feedback check loop completed.")

    @check_feedback_loop .before_loop 
    async def before_check_feedback_loop (self ):
        await self .bot .wait_until_ready ()
        print ("Feedback loop starting...")





@bot .event 
async def on_ready ():

    await load_commands ()


    if not check_premium_expirations .is_running ():
        check_premium_expirations .start ()


    try :
        await bot .add_cog (AutoFeedbackLoop (bot ))
        print ("AutoFeedbackLoop cog loaded successfully.")
    except Exception as e :
        print (f"Error loading AutoFeedbackLoop cog: {e }")


    await bot .tree .sync ()


    dev_guild =discord .Object (id =DEV_CHAMBER_GUILD_ID )
    await bot .tree .sync (guild =dev_guild )


    try :
        await bot .load_extension ("message_listeners.user_blacklisted")
        print ("blacklist_user_listener cog loaded successfully.")
    except Exception as e :
        print (f"Error loading blacklist_user_listener cog: {e }")



    try :
        await bot .load_extension ("message_listeners.blacklisted_wallet")
        print ("blacklist_wallet_listener cog loaded successfully.")
    except Exception as e :
        print (f"Error loading blacklist_wallet_listener cog: {e }")


    try :
        await bot .load_extension ("message_listeners.server_blacklisted")
        print ("server_blacklisted_listener cog loaded successfully.")
    except Exception as e :
        print (f"Error loading server_blacklisted_listener cog: {e }")




    bot .add_view (RecoveryView ())
    print ("Persistent RecoveryView registered!")


    print ("Bot is ready. Global and guild-specific commands have been synced.")
    print (f"Bot is running on {bot .shard_count } shards.")
    await bot .change_presence (
    activity =discord .Activity (type =discord .ActivityType .watching ,name ="discord.gg/LumenBot")
    )

@bot .event 
async def on_message (message ):

    if message .author .bot :
        return 


    if message .reference and message .reference .resolved :
        if message .reference .resolved .author .id ==bot .user .id :
            return 


    if bot .user .mentioned_in (message ):
        if "@everyone"not in message .content and "@here"not in message .content :
            await message .channel .send (
            "Hello! How can I assist you today? Use +invite to get started or +help if you need help."
            )

    await bot .process_commands (message )

@bot .event 
async def on_guild_join (guild ):

    if len (bot .guilds )>95 :
        print (f"Server limit reached (95 servers). Leaving guild: {guild .name } (ID: {guild .id })")
        await guild .leave ()
    else :
        print (f"Joined guild: {guild .name } (ID: {guild .id })")


bot .run (BOT_TOKEN )
