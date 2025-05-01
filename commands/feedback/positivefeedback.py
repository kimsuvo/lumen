
import discord 
from discord .ext import commands 
import asyncio 
import sqlite3 
import re 
import pytz 
from datetime import datetime ,timedelta 
import unicodedata 
import os 
import random 
import config 


from functions .register_functions .registration_functions import (
is_user_registered ,
user_exists_in_any_db ,
generate_unique_key ,
get_current_db_path ,
initialize_database ,
RegisterModal ,
RegisterButton ,
ShowKeyButton 
)


from functions .feedback_functions .check_user_blacklist_ban_functions import user_exists_in_ban_db ,is_user_blacklisted 


from functions .premium_functions .premium_user_functions import is_user_premium 


from functions .feedback_functions .pos_feedback_functions import create_feedback_db ,load_pending_feedback ,generate_vouch_number 


kolkatatz =pytz .timezone ('Asia/Kolkata')

class PrePositiveFeedbackCog (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .current_db_index =0 
        self .current_premium_db_index =0 
        self .load_current_db_index ()
        self .load_current_premium_db_index ()


    def load_current_db_index (self ):
        index_file =os .path .join ("pendingfeedbackdatabase","db_index.txt")
        if os .path .exists (index_file ):
            with open (index_file ,"r")as f :
                try :
                    self .current_db_index =int (f .read ())
                except ValueError :
                    self .current_db_index =0 
        else :
            self .current_db_index =0 

    def save_current_db_index (self ):
        index_file =os .path .join ("pendingfeedbackdatabase","db_index.txt")
        with open (index_file ,"w")as f :
            f .write (str (self .current_db_index ))

    def load_current_premium_db_index (self ):
        index_file =os .path .join ("premiumpendingfeedback","premium_pos_db_index.txt")
        if os .path .exists (index_file ):
            with open (index_file ,"r")as f :
                try :
                    self .current_premium_db_index =int (f .read ())
                except ValueError :
                    self .current_premium_db_index =0 
        else :
            self .current_premium_db_index =0 

    def save_current_premium_db_index (self ):
        index_file =os .path .join ("premiumpendingfeedback","premium_pos_db_index.txt")
        with open (index_file ,"w")as f :
            f .write (str (self .current_premium_db_index ))


    last_vouch_time ={}

    def can_vouch_again (self ,user_id ):
        now =datetime .now (kolkatatz )
        last_time =self .last_vouch_time .get (user_id )
        if last_time and now -last_time <timedelta (seconds =10 ):
            return False 
        self .last_vouch_time [user_id ]=now 
        return True 

    @commands .command (name ="positivefeedback",aliases =["rep","vouch"])
    async def positive_feedback_prefix (self ,ctx ,user :discord .User =None ,*,feedback :str =None ):
        if not user or not feedback :
            embed =discord .Embed (
            title ="**Error**",
            description ="You must mention a user and provide feedback.\n\n**Correct Usage:** `+rep @user Your feedback here`",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =10 )
            return 

        if len (feedback )<15 :
            embed =discord .Embed (
            title ="**Error**",
            description ="Feedback must be at least 15 characters long.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if len (feedback )>100 :
            embed =discord .Embed (
            title ="**Error**",
            description ="Feedback must not exceed 100 characters.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        allowed_symbols ={"|","(",")","[","]","{","}",".",",","•","!",":","-","+",'"',"%","/","\\","?","<",">","~"}
        for char in feedback :
            if unicodedata .category (char ).startswith ("S")and unicodedata .category (char )!="Sc"and char not in allowed_symbols :
                embed =discord .Embed (
                title ="**Error**",
                description ="Feedback must not contain any emoji or disallowed symbol characters.",
                color =0xFF0000 
                )
                error_message =await ctx .send (embed =embed )
                await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
                await error_message .delete (delay =5 )
                return 

        if ctx .author .id ==user .id :
            embed =discord .Embed (
            title ="**Error**",
            description ="You cannot give feedback to yourself.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if user .bot :
            embed =discord .Embed (
            title ="**Error**",
            description ="You cannot give feedback to a bot.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if is_user_blacklisted (ctx .author .id ):
            embed =discord .Embed (
            title ="**Error**",
            description ="You are blacklisted and cannot use this command.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if is_user_blacklisted (user .id ):
            embed =discord .Embed (
            title ="**User Blacklisted**",
            description =f"User `{user .name }` is blacklisted and cannot receive feedback.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if not self .can_vouch_again (ctx .author .id ):
            embed =discord .Embed (
            title ="**Error**",
            description ="You must wait at least 10 seconds before giving another vouch.",
            color =0xff0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        pending_feedbacks =load_pending_feedback ()

        if not is_user_registered (user .id ):
            embed =discord .Embed (
            title ="**The user isn't registered with Lumen!**",
            description =f"The user `{user .name }` is not registered with Lumen.",
            color =0x000001 
            )
            message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await asyncio .sleep (10 )
            await message .delete ()

            try :
                dm_embed =discord .Embed (
                title ="**Feedback Notification System**",
                description =(
                f"Hello! You’ve just received feedback from **{ctx .author .name }**.\n\n"
                "**__Unfortunately, you're not registered with us yet!__**\n"
                "You cannot view or manage your feedback until you create an account.\n\n"
                "**__How to Register:__**\n"
                "Click **Register Now** below to get started."
                ),
                color =0x000001 
                )
                dm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
                view =discord .ui .View ()
                view .add_item (RegisterButton (authorized_user =user ))
                await user .send (embed =dm_embed ,view =view )
            except discord .Forbidden :
                await ctx .send (f"Could not send a DM to <@{user .id }> (DMs are closed).")
            return 

        existing_vouch_numbers =[fb ['vouch_number']for fb in pending_feedbacks ]
        vouch_number =generate_vouch_number (existing_vouch_numbers )
        pending_feedback ={
        "vouch_number":vouch_number ,
        "giver_id":str (ctx .author .id ),
        "receiver_id":str (user .id ),
        "feedback":feedback ,
        "timestamp":datetime .now (kolkatatz ).strftime ("%Y-%m-%d %H:%M:%S"),
        "type":"positive"
        }


        if is_user_premium (user .id ):
            premium_batch_index =self .current_premium_db_index 
            db_path =os .path .join ("premiumpendingfeedback",f"premium_pending_fb_{premium_batch_index +1 }.db")
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ('''
                CREATE TABLE IF NOT EXISTS pending_feedback (
                    vouch_number TEXT PRIMARY KEY,
                    giver_id TEXT,
                    receiver_id TEXT,
                    feedback TEXT,
                    timestamp TEXT,
                    type TEXT
                )
            ''')
            conn .commit ()
            cursor .execute (''' 
                INSERT OR REPLACE INTO pending_feedback 
                (vouch_number, giver_id, receiver_id, feedback, timestamp, type) 
                VALUES (?, ?, ?, ?, ?, ?) 
            ''',(
            pending_feedback ["vouch_number"],
            pending_feedback ["giver_id"],
            pending_feedback ["receiver_id"],
            pending_feedback ["feedback"],
            pending_feedback ["timestamp"],
            pending_feedback ["type"]
            ))
            conn .commit ()
            conn .close ()
            self .current_premium_db_index =(self .current_premium_db_index +1 )%10 
            batch_number =premium_batch_index +1 
            self .save_current_premium_db_index ()
            pending_channel_id =getattr (config ,"PREMIUM_PENDING_FEEDBACK_CHANNEL_ID",None )
            if pending_channel_id is None :
                print ("PREMIUM_PENDING_FEEDBACK_CHANNEL_ID is not set in config.py")
                return 
            pending_channel =ctx .guild .get_channel (pending_channel_id )or await ctx .bot .fetch_channel (pending_channel_id )
            ping_role_id =getattr (config ,f"PREMIUM_FB_BATCH_{batch_number }_PING",None )
            ping_text =f"<@&{ping_role_id }>"if ping_role_id else ""
        else :
            normal_batch_index =self .current_db_index 
            db_path =os .path .join ("pendingfeedbackdatabase",f"pending_fb_{normal_batch_index +1 }.db")
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute (''' 
                INSERT OR REPLACE INTO pending_feedback 
                (vouch_number, giver_id, receiver_id, feedback, timestamp, type) 
                VALUES (?, ?, ?, ?, ?, ?) 
            ''',(
            pending_feedback ["vouch_number"],
            pending_feedback ["giver_id"],
            pending_feedback ["receiver_id"],
            pending_feedback ["feedback"],
            pending_feedback ["timestamp"],
            pending_feedback ["type"]
            ))
            conn .commit ()
            conn .close ()
            self .current_db_index =(self .current_db_index +1 )%10 
            self .save_current_db_index ()
            batch_number =normal_batch_index +1 
            pending_channel =ctx .guild .get_channel (config .PENDING_FEEDBACK_CHANNEL_ID )or await ctx .bot .fetch_channel (config .PENDING_FEEDBACK_CHANNEL_ID )
            ping_role_id =getattr (config ,f"FB_BATCH_{batch_number }_PING",None )
            ping_text =f"<@&{ping_role_id }>"if ping_role_id else ""

        await ctx .message .add_reaction ("<:lumen_online:1324983167538696303>")
        embed =discord .Embed (
        title ="**Feedback Submitted!**",
        description =f"Your feedback for `{user .name }` has been successfully submitted.\n-# It will be reviewed shortly.",
        color =0x000001 
        )
        confirmation_message =await ctx .send (embed =embed )
        await confirmation_message .delete (delay =10 )

        staff_embed =discord .Embed (
        title ="**New Positive Feedback Received**",
        description =(
        f"-# **Feedback ID:** `{vouch_number }`\n"
        f"-# **Giver:** <@{ctx .author .id }>\n"
        f"-# **Receiver:** <@{user .id }>\n"
        f"-# **Feedback:** {feedback }\n"
        f"-# **Timestamp:** {datetime .now (kolkatatz ).strftime ('%Y-%m-%d %H:%M:%S')}"
        ),
        color =0x000001 ,
        timestamp =datetime .now (kolkatatz )
        )
        staff_embed .add_field (name ="BATCH",value =str (batch_number ),inline =False )
        staff_embed .set_footer (text ="Feedback System Notification")
        await pending_channel .send (content =ping_text ,embed =staff_embed )

        try :
            dm_embed =discord .Embed (
            title ="**Feedback Received**",
            description =(
            f"<:lumen_online:1324983167538696303> You have received positive feedback from `{ctx .author .name }`.\n"
            f"The ID of this feedback is `{vouch_number }`.\n"
            "-# Once approved, the vouch will be recorded in your profile."
            ),
            color =0x000001 
            )
            await user .send (embed =dm_embed )
        except discord .Forbidden :
            await ctx .send (f"Could not send a DM to <@{user .id }> (DMs are closed).")

async def setup (bot ):
    cog =PrePositiveFeedbackCog (bot )
    create_feedback_db ()
    await bot .add_cog (cog )
