import discord 
from discord .ext import commands 
import sqlite3 
import os 
from config import (
FEEDBACK_ADMIN_ROLE ,
FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ,
PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,
PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 
)


VERIFICATION_DATABASE_DIR ="verificationdatabase"
PREMIUM_VERIFICATION_DATABASE_DIR ="premiumverificationfeedback"

def create_db_connection (db_path ):
    """Helper function to create and return a database connection."""
    conn =sqlite3 .connect (db_path )
    return conn 

class ViewVerificationFeedback (commands .Cog ):
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

    @commands .command (aliases =["viewpendingverification","pfvall"])
    async def view_pending_verification (self ,ctx ):
        try :

            if not any (role .id in FEEDBACK_ADMIN_ROLE for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="**Permission Required**",
                description ="You do not have the required permissions to use this command.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 



            user_roles =[role .id for role in ctx .author .roles ]



            all_batch_role_ids =(
            [role for roles in self .premium_batch_roles .values ()for role in roles ]+
            [role for roles in self .standard_batch_roles .values ()for role in roles ]
            )

            user_batch_roles =[role_id for role_id in user_roles if role_id in all_batch_role_ids ]


            if len (user_batch_roles )>1 :
                embed =discord .Embed (
                title ="**Multiple Batch Roles Detected**",
                description ="You have more than one batch role assigned. Please contact an administrator.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 



            batch_number =None 
            database_dir =None 
            db_prefix =None 


            for num ,role_ids in self .premium_batch_roles .items ():
                if any (r in user_roles for r in role_ids ):
                    batch_number =num 
                    database_dir =PREMIUM_VERIFICATION_DATABASE_DIR 
                    db_prefix ="premium_verification_fb"
                    break 



            if batch_number is None :
                for num ,role_ids in self .standard_batch_roles .items ():
                    if any (r in user_roles for r in role_ids ):
                        batch_number =num 
                        database_dir =VERIFICATION_DATABASE_DIR 
                        db_prefix ="verification_fb"
                        break 


            if batch_number is None :
                embed =discord .Embed (
                title ="**Batch Role Required**",
                description ="You do not have any valid FB_BATCH_x or PREMIUM_FB_BATCH_x role assigned. Please contact an administrator.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            batch_type ="Premium"if db_prefix .startswith ("premium")else "Standard"


            verification_db_name =f"{db_prefix }_{batch_number }.db"
            verification_db_path =os .path .join (database_dir ,verification_db_name )


            if not os .path .exists (verification_db_path ):
                embed =discord .Embed (
                title ="**Database Not Found**",
                description =f"The verification database for batch {batch_number } does not exist.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            initial_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> **Fetching Pending Feedbacks...**",
            description =f"Batch {batch_number }: Please wait while I retrieve the pending feedbacks for verification.",
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
                description ="There are no pending feedbacks for verification in your batch.",
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
                embed =discord .Embed (
                title =f"Pending Verification Feedbacks (Batch {batch_number }, {batch_type }) - Page {idx +1 }/{total_pages }",
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


async def setup (bot ):
    await bot .add_cog (ViewVerificationFeedback (bot ))
