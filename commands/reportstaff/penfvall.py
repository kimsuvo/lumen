import discord 
from discord .ext import commands 
import sqlite3 
from config import REPORT_STAFF_ROLE 
import os 


VERIFICATION_DATABASE_DIR ="verificationdatabase"
PREMIUM_VERIFICATION_DATABASE_DIR ="premiumverificationfeedback"

def create_db_connection (db_path ):
    """Helper function to create and return a database connection."""
    conn =sqlite3 .connect (db_path )
    return conn 

class PFBVAll (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="penfvall",aliases =["viewpendingfeedbackverification"])
    async def penfvall (self ,ctx ,batch_identifier :str ):
        """
        Fetches pending verification feedbacks for the specified batch.
        Usage:
          +penfvall 1  -> fetches from verification_fb_1.db in the verificationdatabase directory.
          +penfvall p1 -> fetches from premium_verification_fb_1.db in the premiumverificationfeedback directory.
        This command can only be used by users with the REPORT_STAFF_ROLE.
        """
        try :

            if not any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="**Permission Required**",
                description ="You do not have the required permissions to use this command.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 



            is_premium =False 
            batch_number_str =batch_identifier 

            if batch_identifier .lower ().startswith ("p"):
                is_premium =True 
                batch_number_str =batch_identifier [1 :]

            try :
                batch_number =int (batch_number_str )
            except ValueError :
                embed =discord .Embed (
                title ="**Invalid Batch Number**",
                description ="The batch number must be an integer (e.g., `1` or `p1`).",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            if batch_number <1 :
                embed =discord .Embed (
                title ="**Invalid Batch Number**",
                description ="The batch number must be a positive integer.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            if is_premium :
                db_name =f"premium_verification_fb_{batch_number }.db"
                db_dir =PREMIUM_VERIFICATION_DATABASE_DIR 
            else :
                db_name =f"verification_fb_{batch_number }.db"
                db_dir =VERIFICATION_DATABASE_DIR 

            verification_db_path =os .path .join (db_dir ,db_name )


            if not os .path .exists (verification_db_path ):
                embed =discord .Embed (
                title ="**Incorrect Batch**",
                description =f"The verification database for batch {batch_identifier } does not exist.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            initial_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> **Fetching Pending Feedbacks...**",
            description =f"Batch {batch_identifier }: Please wait while I retrieve the pending feedbacks for verification.",
            color =0x000001 
            )
            message =await ctx .send (embed =initial_embed )


            conn =create_db_connection (verification_db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM pending_feedback")
            feedbacks =cursor .fetchall ()

            if not feedbacks :
                embed =discord .Embed (
                title ="<:lumen_online:1324983167538696303> **No Pending Feedback**",
                description ="There are no pending feedbacks for verification in this batch.",
                color =0x000001 
                )
                await message .delete ()
                await ctx .send (embed =embed )
                conn .close ()
                return 


            chunk_size =15 
            feedback_chunks =[feedbacks [i :i +chunk_size ]for i in range (0 ,len (feedbacks ),chunk_size )]
            total_pages =len (feedback_chunks )

            for idx ,chunk in enumerate (feedback_chunks ):
                current_page =idx +1 
                if is_premium :
                    embed_title =f"Pending Verification Feedbacks (Batch {batch_number }, Premium) - Page {current_page }/{total_pages }"
                else :
                    embed_title =f"Pending Verification Feedbacks (Batch {batch_number }) - Page {current_page }/{total_pages }"

                embed =discord .Embed (
                title =embed_title ,
                description ="Below are the feedbacks pending verification.",
                color =0x000001 
                )

                for feedback in chunk :


                    vouch_number ,giver_id ,receiver_id ,feedback_text ,timestamp ,feedback_type =feedback 


                    if len (feedback_text )>1024 :
                        feedback_text =feedback_text [:1021 ]+"..."

                    embed .add_field (
                    name =f"Feedback #{vouch_number }",
                    value =(
                    f"-# **Giver:** <@{giver_id }>\n"
                    f"-# **Receiver:** <@{receiver_id }>\n"
                    f"-# **Type:** {feedback_type .capitalize ()}\n"
                    f"-# **Feedback:** {feedback_text }\n"
                    f"-# **Verification Requested On:** {timestamp }\n"
                    f"**Feedback ID:** ```{vouch_number }```"
                    ),
                    inline =False 
                    )


                if idx ==0 :
                    await message .delete ()
                await ctx .send (embed =embed )

            conn .close ()

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =f"An error occurred: {e }",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed )


    @penfvall .error 
    async def penfvall_error (self ,ctx ,error ):
        """
        Error handler for the penfvall command.
        Provides user-friendly messages for missing or invalid arguments.
        """
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Missing Argument**",
            description ="Please provide a batch identifier.\nUsage: `+penfvall <batch number>` or `+penfvall p<batch number>`",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
        elif isinstance (error ,commands .BadArgument ):
            embed =discord .Embed (
            title ="**Invalid Argument**",
            description ="The batch identifier must be an integer or in the format `p<number>` for premium batches.\nUsage: `+penfvall <batch number>` or `+penfvall p<batch number>`",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="Error",
            description =f"An unexpected error occurred: {error }",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (PFBVAll (bot ))
