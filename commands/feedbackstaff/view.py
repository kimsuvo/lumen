import discord 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
from discord .ui import Button ,View 
import os 
import glob 
from config import GENERAL_STAFF_ROLE 
import re 


def get_last_verification_request_time (user_id ):
    directory ="verifyrequesttime"
    if not os .path .isdir (directory ):
        return "Never"
    db_files =[f for f in os .listdir (directory )if f .startswith ("last_verify_")and f .endswith (".db")]
    if not db_files :
        return "Never"
    def extract_number (filename ):
        try :
            return int (re .search (r'(\d+)',filename ).group (1 ))
        except :
            return 0 
    db_files =sorted (db_files ,key =extract_number ,reverse =True )
    for db_file in db_files :
        db_path =os .path .join (directory ,db_file )
        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT timestamp FROM verify_time WHERE user_id = ?",(str (user_id ),))
            row =cursor .fetchone ()
            conn .close ()
            if row :
                return row [0 ]
        except sqlite3 .Error :
            continue 
    return "Never"




def view_command_db (db_name ):
    return sqlite3 .connect (db_name )


def load_records_from_directory (directory ,table_name ):
    records_list =[]

    if not os .path .isdir (directory ):
        return records_list 

    db_files =[f for f in os .listdir (directory )if f .endswith ('.db')]
    if not db_files :
        return records_list 
    for db_file in db_files :
        db_path =os .path .join (directory ,db_file )
        try :
            conn =view_command_db (db_path )
            cursor =conn .cursor ()

            cursor .execute ("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table_name ,))
            table_exists =cursor .fetchone ()
            if not table_exists :
                continue 

            cursor .execute (f"SELECT * FROM {table_name }")
            records =cursor .fetchall ()
            if not records :
                conn .close ()
                continue 


            match =re .search (r'(\d+)',db_file )
            batch_number =match .group (1 )if match else "Unknown"
            for record in records :


                records_list .append ({
                'vouch_number':record [0 ],
                'giver_id':record [1 ],
                'receiver_id':record [2 ],
                'feedback':record [3 ],
                'timestamp':record [4 ],
                'type':record [5 ],
                'batch':batch_number 
                })
        except sqlite3 .Error :
            continue 
        finally :
            conn .close ()
    return records_list 


def is_user_premium (user_id :int )->bool :
    premium_db_dir ="premiumdatabase"
    db_files =sorted (glob .glob (os .path .join (premium_db_dir ,"*.db")))
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


def fetch_pending_feedbacks (user_id :int ):
    if is_user_premium (user_id ):
        pending_feedback_dir =os .path .join ('premiumpendingfeedback')
    else :
        pending_feedback_dir =os .path .join ('pendingfeedbackdatabase')
    return load_records_from_directory (pending_feedback_dir ,'pending_feedback')



def fetch_pending_verifications (user_id :int ):
    if is_user_premium (user_id ):
        verification_dir =os .path .join ('premiumverificationfeedback')
    else :
        verification_dir =os .path .join ('verificationdatabase')
    return load_records_from_directory (verification_dir ,'pending_feedback')

class FeedbackView (View ):
    def __init__ (self ,ctx ,user ):
        super ().__init__ (timeout =60 )
        self .ctx =ctx 

        self .target_user_id =str (user .id )if user else str (ctx .author .id )

    @discord .ui .button (label ="Pending Feedback",style =discord .ButtonStyle .secondary )
    async def pending_feedback_button (self ,interaction :discord .Interaction ,button :Button ):

        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You are not authorized to interact with this button.",ephemeral =True )
            return 

        await interaction .message .delete ()

        all_feedbacks =fetch_pending_feedbacks (int (self .target_user_id ))
        filtered_feedbacks =[fb for fb in all_feedbacks if str (fb ['receiver_id'])==self .target_user_id ]

        await self .send_feedback_list (interaction ,filtered_feedbacks ,"Pending Feedbacks")

    @discord .ui .button (label ="Pending Verification",style =discord .ButtonStyle .primary )
    async def pending_verification_button (self ,interaction :discord .Interaction ,button :Button ):

        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You are not authorized to interact with this button.",ephemeral =True )
            return 

        await interaction .message .delete ()

        all_verifications =fetch_pending_verifications (int (self .target_user_id ))
        filtered_verifications =[fb for fb in all_verifications if str (fb ['receiver_id'])==self .target_user_id ]

        await self .send_feedback_list (interaction ,filtered_verifications ,"Pending Verifications")

    async def send_feedback_list (self ,interaction ,feedbacks ,title ):

        if not feedbacks :
            embed =discord .Embed (
            description =f"**No {title .lower ()} found for the user.**",
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await interaction .response .send_message (embed =embed )
            return 

        chunk_size =20 
        chunks =[feedbacks [i :i +chunk_size ]for i in range (0 ,len (feedbacks ),chunk_size )]
        for i ,chunk in enumerate (chunks ):
            embed =discord .Embed (
            title =f"**{title } List**",
            description =f"Here are the {title .lower ()} awaiting approval:",
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            for fb in chunk :
                feedback_type ="Positive"if fb ['type']=="positive"else "Negative"
                embed .add_field (
                name =f"Feedback #`{fb ['vouch_number']}`",
                value =(
                f"-# **Feedback Type:** {feedback_type }\n"
                f"-# **Giver:** <@{fb ['giver_id']}>\n"
                f"-# **Receiver:** <@{fb ['receiver_id']}>\n"
                f"-# **Feedback:** {fb ['feedback']}\n"
                f"-# **Timestamp:** {fb ['timestamp']}\n"
                f"-# **Batch:** {fb ['batch']}\n"
                f"**Feedback ID:** ```{fb ['vouch_number']}```"
                ),
                inline =False 
                )

            if len (chunks )>1 :
                embed .set_footer (text =f"Page {i +1 }/{len (chunks )}")
            if i ==0 :
                await interaction .response .send_message (embed =embed )
            else :
                await interaction .followup .send (embed =embed )

class ViewPending (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="view")
    async def view_pending_feedback (self ,ctx ,user :discord .User =None ):

        if not any (role .id in GENERAL_STAFF_ROLE for role in ctx .author .roles ):
            kolkata_tz =pytz .timezone ('Asia/Kolkata')
            timestamp =datetime .now (kolkata_tz )
            embed =discord .Embed (
            title ="**<:lumen_dnd:1324983165554524252> Permission Denied**",
            description ="You do not have permission to view pending feedback.",
            color =0xff0000 ,
            timestamp =timestamp 
            )
            await ctx .send (embed =embed )
            return 

        last_verification =get_last_verification_request_time (ctx .author .id )
        embed =discord .Embed (
        title ="**<:lumen_idle:1324983172219273217> View Pending Feedback**",
        description =(
        "Click on the buttons below to view either pending feedback or pending verification "
        f"for {'yourself'if not user else user .name }."
        ),
        color =0x000001 ,
        timestamp =datetime .now (pytz .utc )
        )
        embed .add_field (name ="Last Verification Requested on:",value =last_verification ,inline =False )

        view =FeedbackView (ctx ,user )
        await ctx .send (embed =embed ,view =view )

async def setup (bot ):
    await bot .add_cog (ViewPending (bot ))