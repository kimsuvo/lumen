import discord 
from discord .ext import commands 
import os 
import sqlite3 
import asyncio 
from datetime import datetime 
import pytz 
from config import (
GUILD_ID ,
PREMIUM_MEMBER_ROLE ,
REVOKE_PREMIUM_ROLE_ID ,
REVOKE_PREMIUM_CHANNEL_ID 
)

BADGES_DB_DIR ="badgesdatabase"
PREMIUM_DB_DIR ="premiumdatabase"
CREDENTIALS_DB_DIR ="credentialsdatabase"
COLOR_DB_DIR ="colordatabase"
BADGE_TO_REMOVE ="<:lumen_premium_badge:1335561446284857445>"

class RevokePremium (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="revokepremium")
    @commands .has_role (REVOKE_PREMIUM_ROLE_ID )
    async def revoke_premium (self ,ctx ,user :discord .Member ):
        """Manually revoke a user's premium membership and perform the related cleanup."""
        user_id =str (user .id )


        initial_channel_embed =discord .Embed (
        title ="Revoking Premium Membership",
        description =f"Revoking premium for user **{user }** (ID: {user_id })...",
        color =0x000001 
        )
        cmd_msg =await ctx .send (embed =initial_channel_embed )


        log_channel =self .bot .get_channel (REVOKE_PREMIUM_CHANNEL_ID )
        initial_log_embed =discord .Embed (
        title ="Revoking Premium Membership",
        description =f"Revoking premium for user **{user }** (ID: {user_id })...",
        color =0x000001 
        )
        log_msg =await log_channel .send (embed =initial_log_embed )


        premium_files =[f for f in os .listdir (PREMIUM_DB_DIR )if f .startswith ("premium_")and f .endswith (".db")]
        for premium_file in premium_files :
            db_path =os .path .join (PREMIUM_DB_DIR ,premium_file )
            try :
                conn =sqlite3 .connect (db_path )
                c =conn .cursor ()
                c .execute ("DELETE FROM premium WHERE user_id = ?",(user_id ,))
                conn .commit ()
            except Exception :
                pass 
            finally :
                conn .close ()


        guild =self .bot .get_guild (GUILD_ID )
        if guild :
            member =guild .get_member (int (user_id ))
            if member :
                role =guild .get_role (PREMIUM_MEMBER_ROLE )
                if role and role in member .roles :
                    try :
                        await member .remove_roles (role )
                    except Exception :
                        pass 


        badge_files =[f for f in os .listdir (BADGES_DB_DIR )if f .startswith ("badges_")and f .endswith (".db")]
        for badges_file in badge_files :
            badges_db_path =os .path .join (BADGES_DB_DIR ,badges_file )
            try :
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
            except Exception :
                pass 
            finally :
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
                except Exception :
                    pass 
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
                except Exception :
                    pass 
                finally :
                    if conn_prod :
                        conn_prod .close ()


        image_files =[f for f in os .listdir ("imagedatabase")if f .startswith ("image_")and f .endswith (".db")]
        for image_file in image_files :
            image_db_path =os .path .join ("imagedatabase",image_file )
            try :
                conn_image =sqlite3 .connect (image_db_path )
                c_image =conn_image .cursor ()
                c_image .execute ("DELETE FROM imagethumbnail WHERE user_id = ?",(user_id ,))
                conn_image .commit ()
            except Exception :
                pass 
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
            except Exception :
                pass 
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
            except Exception :
                pass 
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
                except Exception :
                    pass 
                finally :
                    conn_cb .close ()


        store_button_dir ="buttonsdatabase"
        if os .path .exists (store_button_dir ):
            sb_files =[f for f in os .listdir (store_button_dir )if f .endswith (".db")]
            for sb_file in sb_files :
                sb_db_path =os .path .join (store_button_dir ,sb_file )
                try :
                    conn_cb =sqlite3 .connect (sb_db_path )
                    c_cb =conn_cb .cursor ()
                    c_cb .execute ("DELETE FROM buttons WHERE user_id = ?",(user_id ,))
                    conn_cb .commit ()
                    print (f"Removed store button entry for user {user_id } from {sb_file }.")
                except Exception as e :
                    print (f"Error removing store button entry for user {user_id } from {sb_file }: {e }")
                finally :
                    conn_cb .close ()


        try :
            dm_channel =await user .create_dm ()
            dm_embed =discord .Embed (
            title ="Lumen Premium Revoked",
            description =(
            "Your Lumen premium membership has been revoked by an administrator.\n\n"
            "If you believe this is an error or have any questions, please contact our support team."
            ),
            color =0x000001 
            )
            dm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
            view =discord .ui .View ()
            support_button =discord .ui .Button (
            label ="Lumen Support Server",
            url ="https://discord.gg/lumenreport",
            style =discord .ButtonStyle .link 
            )
            view .add_item (support_button )
            await dm_channel .send (embed =dm_embed ,view =view )
        except Exception :
            pass 


        success_channel_embed =discord .Embed (
        title ="Premium Revoked",
        description ="Premium membership has been successfully revoked.",
        color =0x000001 
        )
        await cmd_msg .edit (embed =success_channel_embed )


        ist =pytz .timezone ("Asia/Kolkata")
        current_time =datetime .now (ist ).strftime ("%d-%m-%Y %H:%M:%S %Z")
        final_log_embed =discord .Embed (
        title ="Premium Revoked",
        description =f"**Timestamp (IST):** {current_time }",
        color =0x000001 
        )
        final_log_embed .add_field (name ="Revoked By:",value =f"{ctx .author } (ID: {ctx .author .id })",inline =False )
        final_log_embed .add_field (name ="Revoked User ID:",value =user_id ,inline =True )
        final_log_embed .add_field (name ="Revoked Username:",value =user .name ,inline =True )
        final_log_embed .add_field (name ="Revoked User Mention:",value =user .mention ,inline =False )

        await log_msg .edit (embed =final_log_embed )

async def setup (bot :commands .Bot ):
    await bot .add_cog (RevokePremium (bot ))
