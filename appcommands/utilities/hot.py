import discord 
import sqlite3 
import os 
from datetime import datetime ,timedelta 
from discord .ext import commands 
from discord import app_commands 


from dateutil .tz import gettz 
from dateutil .parser import parse as dateutil_parse 


india_tz =gettz ("Asia/Kolkata")

def parse_and_normalize (timestamp_str ):
    """
    Parses a timestamp string and normalizes it to an offset-aware datetime in IST.
    """
    dt =dateutil_parse (timestamp_str )
    if dt .tzinfo is None :
        dt =dt .replace (tzinfo =india_tz )
    return dt 

class HotLeaderboard (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    def get_period_start (self ,period :str )->datetime :
        """
        Returns the datetime marking the start of the chosen period in IST.
        
        - daily: from today's midnight (00:00 AM IST)
        - weekly: from Monday 00:00 AM IST of the current week
        - monthly: from the 1st day of the current month at 00:00 AM IST
        """
        now =datetime .now (india_tz )
        if period =='daily':
            start =now .replace (hour =0 ,minute =0 ,second =0 ,microsecond =0 )
        elif period =='weekly':
            weekday =now .weekday ()
            start_of_week =now -timedelta (days =weekday )
            start =start_of_week .replace (hour =0 ,minute =0 ,second =0 ,microsecond =0 )
        elif period =='monthly':
            start =now .replace (day =1 ,hour =0 ,minute =0 ,second =0 ,microsecond =0 )
        else :
            start =now .replace (hour =0 ,minute =0 ,second =0 ,microsecond =0 )
        return start 

    def get_hot_users_from (self ,start_datetime :datetime ):
        """
        Given a start datetime in IST, returns all users with positive feedback counts
        between start_datetime and now from all databases in the feedbackdatabase directory.
        """
        feedback_dir ='feedbackdatabase'
        start_str =start_datetime .strftime ('%Y-%m-%d %H:%M:%S')
        end_str =datetime .now (india_tz ).strftime ('%Y-%m-%d %H:%M:%S')
        hot_users ={}


        for db_file in os .listdir (feedback_dir ):
            if db_file .endswith ('.db'):
                db_path =os .path .join (feedback_dir ,db_file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()


                cursor .execute ("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'feedback_%'")
                tables =cursor .fetchall ()

                for table in tables :
                    table_name =table [0 ]
                    parts =table_name .split ('_')
                    if len (parts )==2 :
                        user_id =parts [1 ]


                        cursor .execute (f'''
                            SELECT COUNT(*) 
                            FROM {table_name }
                            WHERE feedback_type = 'positive'
                              AND timestamp >= ?
                              AND timestamp <= ?
                        ''',(start_str ,end_str ))
                        positive_feedback_count =cursor .fetchone ()[0 ]


                        hot_users [user_id ]=hot_users .get (user_id ,0 )+positive_feedback_count 

                conn .close ()


        hot_users_sorted =sorted (
        [{'user_id':user_id ,'positive_feedback_count':count }for user_id ,count in hot_users .items ()],
        key =lambda x :x ['positive_feedback_count'],
        reverse =True 
        )

        return hot_users_sorted 

    @app_commands .command (name ="hot",description ="Shows the top 5 users with the most positive feedback for a specified period.")
    @app_commands .describe (period ="Choose the period: daily, weekly, or monthly")
    @app_commands .choices (period =[
    app_commands .Choice (name ="daily",value ="daily"),
    app_commands .Choice (name ="weekly",value ="weekly"),
    app_commands .Choice (name ="monthly",value ="monthly")
    ])
    async def hot (self ,interaction :discord .Interaction ,period :str ):
        """
        Slash command: /hot <daily|weekly|monthly>
        Displays the leaderboard for positive feedback in the specified period.
        """

        valid_periods =['daily','weekly','monthly']
        if period not in valid_periods :
            embed =discord .Embed (
            title ="Missing Arguments",
            description ="Please specify a valid period: daily, weekly, or monthly.",
            color =0x000001 
            )
            await interaction .response .send_message (embed =embed )
            return 


        await interaction .response .defer ()


        start_datetime =self .get_period_start (period )
        hot_users =self .get_hot_users_from (start_datetime )


        title_map ={
        'daily':"**Daily Leaderboard**",
        'weekly':"**Weekly Leaderboard**",
        'monthly':"**Monthly Leaderboard**"
        }
        embed =discord .Embed (title =title_map [period ],color =0x000001 )


        for i ,user in enumerate (hot_users [:5 ]):
            try :
                user_obj =await self .bot .fetch_user (int (user ['user_id']))
                embed .add_field (
                name =f"**RANK {i +1 }:** {user_obj .display_name }",
                value =(f"-# Mention: {user_obj .mention }\n"
                f"-# Positive Feedback: {user ['positive_feedback_count']}"),
                inline =False 
                )
            except discord .NotFound :
                embed .add_field (
                name =f"**RANK {i +1 }:** Unknown User (ID: {user ['user_id']})",
                value =f"-# Positive Feedback: {user ['positive_feedback_count']}",
                inline =False 
                )


        if not hot_users or all (u ['positive_feedback_count']==0 for u in hot_users ):
            embed .description ="No positive feedback found in this period."


        await interaction .edit_original_response (embed =embed )

async def setup (bot ):
    await bot .add_cog (HotLeaderboard (bot ))
