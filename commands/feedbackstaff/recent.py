import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 

import sqlite3 
import os 
from datetime import datetime 
from config import GENERAL_STAFF_ROLE 

class RecentFeedback (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .recent_feedback_cooldown =commands .CooldownMapping .from_cooldown (1 ,10.0 ,commands .BucketType .user )

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command ()
    async def recent (self ,ctx ,user :discord .User =None ):

        if not any (role .id in GENERAL_STAFF_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="Permission Denied",
            description ="You do not have the required role to use this command.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
            return 



        if user is None :
            embed =discord .Embed (
            title ="Error",
            description ="You must specify a user to see their recent feedback.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
            return 

        searching_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Searching Recent Feedbacks...**",
        description =f"Searching for recent feedbacks for {user .name }",
        color =0x000001 
        )
        message =await ctx .send (embed =searching_embed )


        feedback_dir ='feedbackdatabase'


        if not os .path .isdir (feedback_dir ):
            embed =discord .Embed (
            title ="Error",
            description =f"The directory `{feedback_dir }` does not exist.",
            color =discord .Color .red ()
            )
            await message .edit (embed =embed )
            return 


        feedback_files =[f for f in os .listdir (feedback_dir )if f .endswith ('.db')]

        if not feedback_files :
            embed =discord .Embed (
            title ="No Feedback Databases Found",
            description =f"No SQLite database files found in the `{feedback_dir }` directory.",
            color =discord .Color .red ()
            )
            await message .edit (embed =embed )
            return 

        all_feedbacks =[]


        for db_file in feedback_files :
            db_path =os .path .join (feedback_dir ,db_file )
            try :

                feedback_conn =sqlite3 .connect (db_path )
                feedback_cursor =feedback_conn .cursor ()


                table_name =f"feedback_{user .id }"


                feedback_cursor .execute (
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name ,)
                )
                table_exists =feedback_cursor .fetchone ()

                if table_exists :

                    feedback_cursor .execute (
                    f"SELECT giver_id, feedback, feedback_type, timestamp FROM {table_name }"
                    )
                    feedbacks =feedback_cursor .fetchall ()


                    for feedback in feedbacks :
                        all_feedbacks .append (feedback )

            except sqlite3 .Error as e :

                print (f"Error accessing {db_file }: {e }")
                continue 

            finally :

                feedback_conn .close ()


        if not all_feedbacks :
            embed =discord .Embed (
            title ="No Feedback",
            description =f"{user .name } has received no feedback yet.",
            color =discord .Color .red ()
            )
            await message .edit (embed =embed )
            return 


        try :

            sorted_feedbacks =sorted (
            all_feedbacks ,
            key =lambda x :datetime .fromisoformat (x [3 ]),
            reverse =True 
            )
        except ValueError :

            sorted_feedbacks =sorted (
            all_feedbacks ,
            key =lambda x :x [3 ],
            reverse =True 
            )


        recent_feedbacks =sorted_feedbacks [:25 ]


        embed =discord .Embed (title =f"**Recent Feedbacks for {user .name }**",color =0x000001 )

        for feedback in recent_feedbacks :
            giver_id ,feedback_text ,feedback_type ,timestamp =feedback 
            try :
                giver =await self .bot .fetch_user (giver_id )
                giver_name =giver .name 
            except discord .NotFound :
                giver_name ="Unknown User"

            embed .add_field (
            name =f"Feedback from {giver_name }",
            value =(
            f"-# **Type:** {feedback_type }\n"
            f"-# **Feedback:** {feedback_text }\n"
            f"-# **Timestamp:** {timestamp }"
            ),
            inline =False 
            )

        await message .edit (embed =embed )

    @recent .error 
    async def profile_prefix_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):

            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =(
            f"You're on cooldown! Please try again in "
            f"**{error .retry_after :.1f} seconds**."
            ),
            color =discord .Color .red (),
            timestamp =datetime .utcnow ()
            )
            cooldown_embed .set_footer (
            text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )


            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :

            raise error 


async def setup (bot ):
    await bot .add_cog (RecentFeedback (bot ))
