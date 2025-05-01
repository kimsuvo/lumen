import discord 
from discord .ext import commands 
from discord .ui import Button ,View 
import sqlite3 
from datetime import datetime 
from pytz import timezone 
import os 
from config import (
FEEDBACK_ADMIN_ROLE ,
VERIFICATION_FEEDBACK_CHANNEL_ID ,
PREMIUM_VERIFICATION_FEEDBACK_CHANNEL_ID ,
FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ,
PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,
PREMIUM_FB_BATCH_5 ,PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,
PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 
)

import aiohttp 


PENDING_FEEDBACK_DIR ="pendingfeedbackdatabase"
VERIFICATION_DATABASE_DIR ="verificationdatabase"
NUM_DATABASES =10 


PREMIUM_VERIFICATION_DIR ="premiumverificationfeedback"
PREMIUM_PENDING_DIR ="premiumpendingfeedback"


VERIFY_REQUEST_TIME_DIR ="verifyrequesttime"


CREATE_TABLE_QUERY ="""
CREATE TABLE IF NOT EXISTS pending_feedback (
    vouch_number TEXT PRIMARY KEY,
    giver_id TEXT,
    receiver_id TEXT,
    feedback TEXT,
    timestamp TEXT,
    type TEXT
)
"""

def create_db_connection (db_path ):
    """Establish a SQLite database connection."""
    conn =sqlite3 .connect (db_path )
    conn .row_factory =sqlite3 .Row 
    return conn 

def initialize_directories ():
    """Ensure that required directories exist."""
    os .makedirs (PENDING_FEEDBACK_DIR ,exist_ok =True )
    os .makedirs (VERIFICATION_DATABASE_DIR ,exist_ok =True )
    os .makedirs (PREMIUM_VERIFICATION_DIR ,exist_ok =True )
    os .makedirs (PREMIUM_PENDING_DIR ,exist_ok =True )
    os .makedirs (VERIFY_REQUEST_TIME_DIR ,exist_ok =True )

def initialize_databases ():
    """Initialize all pending and verification databases with the required tables."""

    for i in range (1 ,NUM_DATABASES +1 ):
        pending_db_path =os .path .join (PENDING_FEEDBACK_DIR ,f"pending_fb_{i }.db")
        conn =create_db_connection (pending_db_path )
        cursor =conn .cursor ()
        cursor .execute (CREATE_TABLE_QUERY )
        conn .commit ()
        conn .close ()


    for i in range (1 ,NUM_DATABASES +1 ):
        verification_db_path =os .path .join (VERIFICATION_DATABASE_DIR ,f"verification_fb_{i }.db")
        conn =create_db_connection (verification_db_path )
        cursor =conn .cursor ()
        cursor .execute (CREATE_TABLE_QUERY )
        conn .commit ()
        conn .close ()


    for i in range (1 ,NUM_DATABASES +1 ):
        premium_verification_db_path =os .path .join (PREMIUM_VERIFICATION_DIR ,f"premium_verification_fb_{i }.db")
        conn =create_db_connection (premium_verification_db_path )
        cursor =conn .cursor ()
        cursor .execute (CREATE_TABLE_QUERY )
        conn .commit ()
        conn .close ()


    for i in range (1 ,NUM_DATABASES +1 ):
        premium_pending_db_path =os .path .join (PREMIUM_PENDING_DIR ,f"premium_pending_fb_{i }.db")
        conn =create_db_connection (premium_pending_db_path )
        cursor =conn .cursor ()
        cursor .execute (CREATE_TABLE_QUERY )
        conn .commit ()
        conn .close ()


initialize_directories ()
initialize_databases ()


def update_verify_request_time (user_id ):
    """
    Insert or update the user's verification request time in a database file.
    Each database in the VERIFY_REQUEST_TIME_DIR can hold up to 10,000 entries.
    If the current database is full, a new one is created.
    """
    try :
        directory =VERIFY_REQUEST_TIME_DIR 
        os .makedirs (directory ,exist_ok =True )

        def extract_number (filename ):
            try :
                return int (filename .replace ("last_verify_","").replace (".db",""))
            except Exception :
                return 0 


        files =[f for f in os .listdir (directory )if f .startswith ("last_verify_")and f .endswith (".db")]
        files =sorted (files ,key =extract_number )


        if not files :
            new_db_filename ="last_verify_1.db"
            new_db_path =os .path .join (directory ,new_db_filename )
            conn =create_db_connection (new_db_path )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS verify_time (
                    user_id TEXT PRIMARY KEY,
                    timestamp TEXT
                )
            """)
            conn .commit ()
            conn .close ()
            files =[new_db_filename ]


        for f in files :
            db_path =os .path .join (directory ,f )
            conn =create_db_connection (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM verify_time WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            if result :

                timestamp =datetime .now (timezone ("Asia/Kolkata")).strftime ("%Y-%m-%d %H:%M:%S")
                cursor .execute ("UPDATE verify_time SET timestamp = ? WHERE user_id = ?",(timestamp ,str (user_id )))
                conn .commit ()
                conn .close ()
                return 
            conn .close ()



        last_file =files [-1 ]
        last_db_path =os .path .join (directory ,last_file )
        conn =create_db_connection (last_db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT COUNT(*) FROM verify_time")
        count =cursor .fetchone ()[0 ]
        if count <10000 :

            timestamp =datetime .now (timezone ("Asia/Kolkata")).strftime ("%Y-%m-%d %H:%M:%S")
            cursor .execute ("INSERT INTO verify_time (user_id, timestamp) VALUES (?, ?)",(str (user_id ),timestamp ))
            conn .commit ()
            conn .close ()
        else :

            new_number =extract_number (last_file )+1 
            new_db_filename =f"last_verify_{new_number }.db"
            new_db_path =os .path .join (directory ,new_db_filename )
            conn .close ()
            conn =create_db_connection (new_db_path )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS verify_time (
                    user_id TEXT PRIMARY KEY,
                    timestamp TEXT
                )
            """)
            timestamp =datetime .now (timezone ("Asia/Kolkata")).strftime ("%Y-%m-%d %H:%M:%S")
            cursor .execute ("INSERT INTO verify_time (user_id, timestamp) VALUES (?, ?)",(str (user_id ),timestamp ))
            conn .commit ()
            conn .close ()
    except Exception as e :
        print (f"Error updating verify request time for user {user_id }: {e }")


class VouchNumberView (discord .ui .View ):
    def __init__ (self ,vouch_number :str ,*,timeout =86400 ):
        super ().__init__ (timeout =timeout )
        self .vouch_number =vouch_number 


        support_button =Button (label ="Lumen Support Server",url ="https://discord.gg/lumenreport")
        self .add_item (support_button )

    @discord .ui .button (label ="Copy Feedback ID",style =discord .ButtonStyle .secondary )
    async def show_feedback_id (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_message (f"{self .vouch_number }",ephemeral =True )

class PendingVerification (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 


        self .standard_batch_roles ={}
        for batch_num ,roles in enumerate (
        [FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
        FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ],
        start =1 
        ):
            self .standard_batch_roles [batch_num ]=roles 


        self .premium_batch_roles ={}
        for batch_num ,roles in enumerate (
        [PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,
        PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 ],
        start =1 
        ):
            self .premium_batch_roles [batch_num ]=roles 

    def get_user_premium_batch (self ,user_roles ):
        """Determine the premium batch number based on user's roles."""
        premium_batches =[
        num 
        for num ,roles in self .premium_batch_roles .items ()
        if any (role in user_roles for role in roles )
        ]
        if len (premium_batches )==1 :
            return premium_batches [0 ]
        elif len (premium_batches )>1 :
            return "multiple"
        else :
            return None 

    def get_user_batch (self ,user_roles ):
        """Determine the batch number based on user's roles."""
        batch_numbers =[
        num 
        for num ,roles in self .standard_batch_roles .items ()
        if any (role in user_roles for role in roles )
        ]
        if len (batch_numbers )==1 :
            return batch_numbers [0 ]
        elif len (batch_numbers )>1 :
            return "multiple"
        else :
            return None 

    @commands .command (aliases =["vf"])
    async def verifyfeedback (self ,ctx ,vouch_number :str ):
        try :

            if not any (role .id in FEEDBACK_ADMIN_ROLE for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="Missing Permissions",
                description ="You do not have the required permissions to use this command.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            initial_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> Sending Verification Message",
            description ="Sending Verification Message...",
            color =0x000001 
            )
            status_message =await ctx .send (embed =initial_embed )


            user_roles =[role .id for role in ctx .author .roles ]
            premium_batch_number =self .get_user_premium_batch (user_roles )
            if premium_batch_number and premium_batch_number !="multiple":
                is_premium =True 
                batch_number =premium_batch_number 
            else :
                is_premium =False 
                batch_number =self .get_user_batch (user_roles )

            if batch_number =="multiple":
                embed =discord .Embed (
                title ="**Multiple Batch Roles Detected**",
                description ="You have multiple FB_BATCH_x roles assigned. Please ensure you have only one batch role.",
                color =discord .Color .red ()
                )
                await status_message .edit (embed =embed )
                return 

            if not batch_number :
                embed =discord .Embed (
                title ="**Batch Role Required**",
                description ="You do not have any Feedback Batch role assigned. Please contact an administrator.",
                color =discord .Color .red ()
                )
                await status_message .edit (embed =embed )
                return 


            if is_premium :
                pending_db_path =os .path .join (PREMIUM_PENDING_DIR ,f"premium_pending_fb_{batch_number }.db")
            else :
                pending_db_path =os .path .join (PENDING_FEEDBACK_DIR ,f"pending_fb_{batch_number }.db")
                verification_db_path =os .path .join (VERIFICATION_DATABASE_DIR ,f"verification_fb_{batch_number }.db")


            if not os .path .exists (pending_db_path ):
                embed =discord .Embed (
                title ="**Database Not Found**",
                description =f"The pending database for batch `{batch_number }` does not exist.",
                color =discord .Color .red ()
                )
                await status_message .edit (embed =embed )
                return 


            conn =create_db_connection (pending_db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
            feedback =cursor .fetchone ()

            if not feedback :
                embed =discord .Embed (
                title ="**Incorrect Feedback ID**",
                description =f"No feedback found with Feedback ID `{vouch_number }` in Batch `{batch_number }`",
                color =0x000001 
                )
                await status_message .edit (embed =embed )
                conn .close ()
                return 


            embed_color =0x000001 
            embed =discord .Embed (
            title ="**<:lumen_warning:1324983182583664650> Feedback Verification Required**",
            color =embed_color 
            )
            feedback_type =feedback ['type'].capitalize ()
            giver_id =feedback ['giver_id']
            receiver_id =int (feedback ['receiver_id'])

            embed .description =(
            f"You have received the {feedback_type } feedback. Feedback ID `{vouch_number }` from <@{giver_id }>. The Feedback ID is `{vouch_number }`. "
            "This feedback requires manual verification by a staff member.\n"
            "-# Please **[Click here](https://discord.gg/lumenreport)** or visit **https://discord.gg/lumenreport** to open a ticket and provide proof for the feedback.\n\n"
            "**If a ticket is not opened within 24 hours, this feedback will be denied.**\n"
            "-# Repeated occurrences may result in being blacklisted from the feedback system."
            )


            user =await self .bot .fetch_user (receiver_id )
            if user :
                try :
                    view =VouchNumberView (vouch_number )
                    await user .send (embed =embed ,view =view )
                except discord .Forbidden :
                    embed =discord .Embed (
                    title ="**Unable to send the DM**",
                    description =f"Could not send DM to user with ID {receiver_id }. They might have DMs disabled.",
                    color =discord .Color .red ()
                    )
                    await ctx .send (embed =embed )
                    return 

                success_embed =discord .Embed (
                title ="**Feedback Verification Requested**",
                description =f"Verification message sent to <@{receiver_id }> for feedback **#{vouch_number }**.",
                color =0x000001 
                )
                await status_message .edit (embed =success_embed )


                kolkata_timezone =timezone ("Asia/Kolkata")
                timestamp =datetime .now (kolkata_timezone ).strftime ("%Y-%m-%d %H:%M:%S")
                if is_premium :
                    premium_verification_db_path =os .path .join (PREMIUM_VERIFICATION_DIR ,f"premium_verification_fb_{batch_number }.db")
                    verification_conn =create_db_connection (premium_verification_db_path )
                    verification_cursor =verification_conn .cursor ()
                    verification_cursor .execute (
                    "INSERT INTO pending_feedback (vouch_number, giver_id, receiver_id, feedback, timestamp, type) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                    feedback ['vouch_number'],
                    feedback ['giver_id'],
                    feedback ['receiver_id'],
                    feedback ['feedback'],
                    timestamp ,
                    feedback ['type']
                    )
                    )
                    verification_conn .commit ()
                    verification_conn .close ()
                else :
                    verification_conn =create_db_connection (verification_db_path )
                    verification_cursor =verification_conn .cursor ()
                    verification_cursor .execute (
                    "INSERT INTO pending_feedback (vouch_number, giver_id, receiver_id, feedback, timestamp, type) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                    feedback ['vouch_number'],
                    feedback ['giver_id'],
                    feedback ['receiver_id'],
                    feedback ['feedback'],
                    timestamp ,
                    feedback ['type']
                    )
                    )
                    verification_conn .commit ()
                    verification_conn .close ()


                cursor .execute ("DELETE FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
                conn .commit ()
                conn .close ()


                if is_premium :
                    channel =ctx .guild .get_channel (PREMIUM_VERIFICATION_FEEDBACK_CHANNEL_ID )
                else :
                    channel =ctx .guild .get_channel (VERIFICATION_FEEDBACK_CHANNEL_ID )

                log_embed =discord .Embed (
                title ="Feedback Verification Logged",
                description =(f"Feedback **#{vouch_number }** has been requested for verification.\n"
                f"**Type:** {feedback_type }\n"
                f"**Giver:** <@{giver_id }>\n"
                f"**Receiver:** <@{receiver_id }>\n"
                f"**Batch:** {batch_number }\n"
                f"**Verification Requested By:** <@{ctx .author .id }>"),
                color =0x000001 
                )
                if channel :
                    await channel .send (embed =log_embed )
                else :
                    print ("Error: Verification feedback channel not found.")


                update_verify_request_time (ctx .author .id )

            else :
                embed =discord .Embed (
                title ="**Unable to send the DM**",
                description =f"Could not find user with ID {receiver_id } to send DM.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =f"An error occurred: {e }",
            color =discord .Color .red ()
            )
            await status_message .edit (embed =error_embed )

            await self .update_cpinfo (ctx .author .id )
            return 

    async def update_cpinfo (self ,admin_id ):
        try :
            cpinfo_path =os .path .join ("infodatabase","cpinfo.db")
            os .makedirs ("infodatabase",exist_ok =True )
            cpinfo_conn =create_db_connection (cpinfo_path )
            cpinfo_cursor =cpinfo_conn .cursor ()
            cpinfo_cursor .execute ("""
                CREATE TABLE IF NOT EXISTS cpinfo (
                    user_id TEXT PRIMARY KEY,
                    confirm_count INTEGER DEFAULT 0,
                    reject_count INTEGER DEFAULT 0,
                    verify_count INTEGER DEFAULT 0              
                )
            """)
            cpinfo_cursor .execute ("SELECT verify_count FROM cpinfo WHERE user_id = ?",(str (admin_id ),))
            result =cpinfo_cursor .fetchone ()
            if result :
                new_count =result [0 ]+1 
                cpinfo_cursor .execute ("""
                    UPDATE cpinfo
                    SET verify_count = ?
                    WHERE user_id = ?
                """,(new_count ,str (admin_id )))
            else :
                cpinfo_cursor .execute ("""
                    INSERT INTO cpinfo (user_id, verify_count)
                    VALUES (?, ?)
                """,(str (admin_id ),1 ))
            cpinfo_conn .commit ()
            cpinfo_conn .close ()
        except Exception as e :
            print (f"Failed to update cpinfo for user {admin_id }: {e }")

async def setup (bot ):
    await bot .add_cog (PendingVerification (bot ))
