import discord 
from discord .ext import commands 
import sqlite3 
import os 
from config import REPORT_STAFF_ROLE 

class PenAll (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 


        self .NORMAL_DB_DIR =os .path .join ("pendingfeedbackdatabase")
        self .PREMIUM_DB_DIR =os .path .join ("premiumpendingfeedback")

        os .makedirs (self .NORMAL_DB_DIR ,exist_ok =True )
        os .makedirs (self .PREMIUM_DB_DIR ,exist_ok =True )

    def connect_to_pending (self ,db_path ):
        """
        Connect to the pending feedback database at the given db_path.
        This will also create the table if it does not exist.
        """
        conn =sqlite3 .connect (db_path )
        conn .row_factory =sqlite3 .Row 
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
        return conn 

    @commands .command ()
    async def penall (self ,ctx ,batch :str ):
        """
        Fetch and display all pending feedbacks from the specified batch.
        
        Usage examples:
          +penall 1   -> Fetches from "pending_fb_1.db" in the "pendingfeedbackdatabase" directory.
          +penall p2  -> Fetches from "premium_pending_fb_2.db" in the "premiumpendingfeedback" directory.
        """

        if not any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="**Permission Required**",
            description ="You do not have the required permissions to use this command.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 


        try :

            initial_embed =discord .Embed (
            title ="**<a:lumen_loading:1326260453260656735> Searching Pending Feedbacks...**",
            description ="Please wait while we fetch the pending feedbacks.",
            color =0x000001 
            )
            message =await ctx .send (embed =initial_embed )



            is_premium =False 
            batch_number =batch 
            if batch .lower ().startswith ("p"):
                is_premium =True 
                batch_number =batch [1 :]


            if not batch_number .isdigit ():
                error_embed =discord .Embed (
                title ="Error",
                description ="Invalid batch number. Please provide a valid number (e.g., 1 or p2).",
                color =discord .Color .red ()
                )
                await message .edit (embed =error_embed )
                return 


            if is_premium :
                db_dir =self .PREMIUM_DB_DIR 
                db_filename =f"premium_pending_fb_{batch_number }.db"
            else :
                db_dir =self .NORMAL_DB_DIR 
                db_filename =f"pending_fb_{batch_number }.db"

            db_path =os .path .join (db_dir ,db_filename )


            if not os .path .exists (db_path ):
                error_embed =discord .Embed (
                title ="Error",
                description =f"No batch exists for batch number `{batch }`.",
                color =discord .Color .red ()
                )
                await message .edit (embed =error_embed )
                return 


            conn =self .connect_to_pending (db_path )
            cursor =conn .cursor ()

            cursor .execute ("SELECT * FROM pending_feedback")
            pending_feedback =cursor .fetchall ()


            if not pending_feedback :
                embed =discord .Embed (
                title ="<:lumen_online:1324983167538696303> **No Pending Feedbacks**",
                description =f"There are currently no pending feedbacks in batch `{batch }`.",
                color =0x000001 
                )
                await message .edit (embed =embed )
                conn .close ()
                return 


            feedback_chunks =[pending_feedback [i :i +20 ]for i in range (0 ,len (pending_feedback ),20 )]





            for i ,chunk in enumerate (feedback_chunks ):


                batch_title =f"Batch {batch_number }{', Premium'if is_premium else ''}"
                embed =discord .Embed (
                title =f"<:lumen_idle:1324983172219273217> **Pending Feedbacks ({batch_title }) - Page {i +1 }/{len (feedback_chunks )}**",
                color =0x000001 
                )


                for feedback in chunk :
                    embed .add_field (
                    name =f"Feedback #`{feedback ['vouch_number']}`",
                    value =(
                    f"-# **Giver:** <@{feedback ['giver_id']}>\n"
                    f"-# **Receiver:** <@{feedback ['receiver_id']}>\n"
                    f"-# **Type:** {feedback ['type'].capitalize ()}\n"
                    f"-# **Feedback:** {feedback ['feedback']}\n"
                    f"-# **Timestamp:** {feedback ['timestamp']}\n"
                    f"**Feedback ID:** ```{feedback ['vouch_number']}```"
                    ),
                    inline =False 
                    )


                await ctx .send (embed =embed )

            await message .delete ()
            conn .close ()

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =f"An error occurred: {e }",
            color =discord .Color .red ()
            )
            try :
                await message .edit (embed =error_embed )
            except Exception :
                await ctx .send (embed =error_embed )



async def setup (bot ):
    await bot .add_cog (PenAll (bot ))
