import discord 
from discord .ext import commands 
import sqlite3 
import glob 
import os 

class PreTopLeaderboard (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    def get_top_users (self ):

        db_directory ='feedbackcountdatabase'


        db_files =glob .glob (os .path .join (db_directory ,'*.db'))


        aggregated_feedback ={}

        for db_file in db_files :
            try :

                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()


                cursor .execute ("""
                    SELECT receiver_id, total_feedback_count, positive_feedback_count, negative_feedback_count 
                    FROM feedback_count
                """)
                users_feedback =cursor .fetchall ()


                for user in users_feedback :
                    user_id ,total_feedback ,positive_feedback ,negative_feedback =user 

                    if user_id not in aggregated_feedback :
                        aggregated_feedback [user_id ]={
                        'user_id':user_id ,
                        'total_feedback_count':total_feedback ,
                        'positive_feedback_count':positive_feedback ,
                        'negative_feedback_count':negative_feedback 
                        }
                    else :
                        aggregated_feedback [user_id ]['total_feedback_count']+=total_feedback 
                        aggregated_feedback [user_id ]['positive_feedback_count']+=positive_feedback 
                        aggregated_feedback [user_id ]['negative_feedback_count']+=negative_feedback 

            except sqlite3 .Error as e :
                print (f"Error accessing {db_file }: {e }")
            finally :

                conn .close ()


        top_users =list (aggregated_feedback .values ())


        top_users_sorted =sorted (top_users ,key =lambda x :x ['positive_feedback_count'],reverse =True )

        return top_users_sorted 

    @commands .command ()
    async def top (self ,ctx ):

        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Searching...**",
        description ="Please wait while we gather the top ranked users.",
        color =0x000001 
        )
        message =await ctx .send (embed =initial_embed )


        top_users =self .get_top_users ()


        embed =discord .Embed (title ="**Top Feedback Earners of All Time**",color =0x000001 )

        if not top_users :
            embed .description ="No feedback data available."
        else :

            for i ,user in enumerate (top_users [:5 ]):
                user_id =user ['user_id']
                total_feedback =user ['total_feedback_count']
                positive_feedback =user ['positive_feedback_count']
                negative_feedback =user ['negative_feedback_count']


                try :
                    user_obj =await self .bot .fetch_user (user_id )
                    user_name =user_obj .name 
                except discord .NotFound :
                    user_name =f"`{user_id }` (User not found)"
                except discord .HTTPException :
                    user_name =f"`{user_id }` (Error fetching user)"


                embed .add_field (
                name =f"**RANK {i +1 }:** {user_name }",
                value =(
                f"-# **Total Feedback:** {total_feedback }\n"
                f"-# **Positive Feedback:** {positive_feedback }\n"
                f"-# **Negative Feedback:** {negative_feedback }"
                ),
                inline =False 
                )



        await message .edit (embed =embed )

async def setup (bot ):
    await bot .add_cog (PreTopLeaderboard (bot ))
