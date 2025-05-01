import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 
import sqlite3 
from datetime import datetime 
import pytz 
import os 

def get_feedback_from_db (db_path ,table_name ,vouch_number ):
    """
    Opens the database at db_path and returns the first matching feedback record
    from the specified table based on the vouch_number.
    """
    try :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        query =f"SELECT * FROM {table_name } WHERE vouch_number = ?"
        cursor .execute (query ,(vouch_number ,))
        feedback =cursor .fetchone ()
        conn .close ()
        return feedback 
    except Exception as e :
        print (f"Error reading from {db_path }: {e }")
        return None 

def get_feedback_from_directory (directory ,table_name ,vouch_number ):
    """
    Iterates through all .db files in the given directory and returns a tuple of 
    (feedback, filename) for the first feedback record that matches the vouch_number
    from the specified table.
    """
    if not os .path .exists (directory ):
        return None ,None 

    for filename in os .listdir (directory ):
        if filename .endswith (".db"):
            db_path =os .path .join (directory ,filename )
            feedback =get_feedback_from_db (db_path ,table_name ,vouch_number )
            if feedback :
                return feedback ,filename 
    return None ,None 

def extract_batch (db_filename ):
    """
    Determines the batch information based on the database filename.
    
    For:
      - pending_fb_{number}.db       --> returns "{number}"
      - verification_fb_{number}.db    --> returns "{number}"
      - premium_pending_fb_{number}.db --> returns "Premium {number}"
      - premium_verification_fb_{number}.db --> returns "Premium {number}"
      - rejected_fb_{any}.db           --> returns "Management"
    """
    if not db_filename :
        return "Unknown"

    base =os .path .splitext (db_filename )[0 ]
    if base .startswith ("pending_fb_"):
        batch_number =base .replace ("pending_fb_","")
        return batch_number 
    elif base .startswith ("verification_fb_"):
        batch_number =base .replace ("verification_fb_","")
        return batch_number 
    elif base .startswith ("premium_pending_fb_"):
        batch_number =base .replace ("premium_pending_fb_","")
        return f"Premium {batch_number }"
    elif base .startswith ("premium_verification_fb_"):
        batch_number =base .replace ("premium_verification_fb_","")
        return f"Premium {batch_number }"
    elif base .startswith ("rejected_fb_"):
        return "Management"
    else :
        return "Unknown"

class PreFeedbackStatus (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command (name ="fbstatus")
    async def feedback_status (self ,ctx ,vouch_number :str ):

        feedback ,db_filename =get_feedback_from_directory ("pendingfeedbackdatabase","pending_feedback",vouch_number )
        if feedback :
            batch =extract_batch (db_filename )
            embed =discord .Embed (
            title ="**<:lumen_idle:1324983172219273217> Pending Feedback**",
            description =(
            f"**Feedback #`{feedback [0 ]}`**\n"
            f"-# **Feedback Type:** {'Positive'if feedback [5 ].lower ()=='positive'else 'Negative'}\n"
            f"-# **Giver:** <@{feedback [1 ]}>\n"
            f"-# **Receiver:** <@{feedback [2 ]}>\n"
            f"-# **Feedback:** {feedback [3 ]}\n"
            f"-# **Timestamp:** {feedback [4 ]}\n"
            f"-# **Batch:** {batch }\n"
            ),
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await ctx .send (embed =embed )
            return 


        feedback ,db_filename =get_feedback_from_directory ("premiumpendingfeedback","pending_feedback",vouch_number )
        if feedback :
            batch =extract_batch (db_filename )
            embed =discord .Embed (
            title ="**<:lumen_idle:1324983172219273217> Premium Pending Feedback**",
            description =(
            f"**Feedback #`{feedback [0 ]}`**\n"
            f"-# **Feedback Type:** {'Positive'if feedback [5 ].lower ()=='positive'else 'Negative'}\n"
            f"-# **Giver:** <@{feedback [1 ]}>\n"
            f"-# **Receiver:** <@{feedback [2 ]}>\n"
            f"-# **Feedback:** {feedback [3 ]}\n"
            f"-# **Timestamp:** {feedback [4 ]}\n"
            f"-# **Batch:** {batch }\n"
            ),
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await ctx .send (embed =embed )
            return 


        feedback ,db_filename =get_feedback_from_directory ("verificationdatabase","pending_feedback",vouch_number )
        if feedback :
            batch =extract_batch (db_filename )
            embed =discord .Embed (
            title ="**<:lumen_idle:1324983172219273217> Pending Verification**",
            description =(
            f"**Feedback #`{feedback [0 ]}`**\n"
            f"-# **Feedback Type:** {'Positive'if feedback [5 ].lower ()=='positive'else 'Negative'}\n"
            f"-# **Giver:** <@{feedback [1 ]}>\n"
            f"-# **Receiver:** <@{feedback [2 ]}>\n"
            f"-# **Feedback:** {feedback [3 ]}\n"
            f"-# **Timestamp:** {feedback [4 ]}\n"
            f"-# **Batch:** {batch }\n"
            ),
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await ctx .send (embed =embed )
            return 


        feedback ,db_filename =get_feedback_from_directory ("premiumverificationfeedback","pending_feedback",vouch_number )
        if feedback :
            batch =extract_batch (db_filename )
            embed =discord .Embed (
            title ="**<:lumen_idle:1324983172219273217> Premium Pending Verification**",
            description =(
            f"**Feedback #`{feedback [0 ]}`**\n"
            f"-# **Feedback Type:** {'Positive'if feedback [5 ].lower ()=='positive'else 'Negative'}\n"
            f"-# **Giver:** <@{feedback [1 ]}>\n"
            f"-# **Receiver:** <@{feedback [2 ]}>\n"
            f"-# **Feedback:** {feedback [3 ]}\n"
            f"-# **Timestamp:** {feedback [4 ]}\n"
            f"-# **Batch:** {batch }\n"
            ),
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await ctx .send (embed =embed )
            return 


        feedback ,db_filename =get_feedback_from_directory ("rejectedfeedbacks","rejected_feedback",vouch_number )
        if feedback :
            batch =extract_batch (db_filename )
            embed =discord .Embed (
            title ="**<:lumen_dnd:1324983165554524252> Rejected Feedback**",
            description =(
            f"**Feedback #`{feedback [0 ]}`**\n"
            f"-# **Feedback Type:** {'Positive'if feedback [5 ].lower ()=='positive'else 'Negative'}\n"
            f"-# **Giver:** <@{feedback [1 ]}>\n"
            f"-# **Receiver:** <@{feedback [2 ]}>\n"
            f"-# **Feedback:** {feedback [3 ]}\n"
            f"-# **Timestamp:** {feedback [4 ]}\n"
            f"-# **Batch:** {batch }\n"
            ),
            color =0x000001 ,
            timestamp =datetime .now (pytz .utc )
            )
            await ctx .send (embed =embed )
            return 


        embed =discord .Embed (
        title ="**<:lumen_offline:1324983152170500147> Feedback Not Found**",
        description =(f"No feedback found with vouch number `{vouch_number }`. "
        "It is either approved or doesn't exist."),
        color =0x000001 ,
        timestamp =datetime .now (pytz .utc )
        )
        await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (PreFeedbackStatus (bot ))
