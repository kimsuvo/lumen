import discord 
from discord .ext import commands 
import sqlite3 
import os 
from config import (
FEEDBACK_ADMIN_ROLE ,
FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ,
PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,PREMIUM_FB_BATCH_6 ,
PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 
)

class PendingAll (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 


        self .PENDING_FEEDBACK_DB_DIR =os .path .join ("pendingfeedbackdatabase")
        self .PREMIUM_PENDING_FEEDBACK_DB_DIR =os .path .join ("premiumpendingfeedback")


        os .makedirs (self .PENDING_FEEDBACK_DB_DIR ,exist_ok =True )
        os .makedirs (self .PREMIUM_PENDING_FEEDBACK_DB_DIR ,exist_ok =True )


        self .FB_BATCH_ROLES ={}
        for batch_number ,role_ids in enumerate (
        [FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
        FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ],
        start =1 
        ):
            for role_id in role_ids :
                self .FB_BATCH_ROLES [role_id ]=batch_number 


        self .PREMIUM_FB_BATCH_ROLES ={}
        for batch_number ,role_ids in enumerate (
        [PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,
        PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 ],
        start =1 
        ):
            for role_id in role_ids :
                self .PREMIUM_FB_BATCH_ROLES [role_id ]=batch_number 




    def connect_to_pending (self ,batch_number :int ,pending_type :str ="normal"):
        """
        Connect to the appropriate pending_feedback database based on batch number and type.
        :param batch_number: The batch number to use.
        :param pending_type: "normal" or "premium"
        :return: sqlite3 Connection object.
        """
        if pending_type =="premium":
            db_filename =f"premium_pending_fb_{batch_number }.db"
            db_dir =self .PREMIUM_PENDING_FEEDBACK_DB_DIR 
        else :
            db_filename =f"pending_fb_{batch_number }.db"
            db_dir =self .PENDING_FEEDBACK_DB_DIR 

        db_path =os .path .join (db_dir ,db_filename )

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

    @commands .command (aliases =["pall"])
    async def pendingall (self ,ctx ):

        if not any (role .id in FEEDBACK_ADMIN_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="**Permission Required**",
            description ="You do not have the required permissions to use this command.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 

        user_roles =ctx .author .roles 



        batch_roles =[
        role .id for role in user_roles 
        if role .id in self .PREMIUM_FB_BATCH_ROLES or role .id in self .FB_BATCH_ROLES 
        ]
        if len (batch_roles )>1 :
            embed =discord .Embed (
            title ="Multiple Batch Roles Found",
            description ="You have more than one batch role. Please ensure you only have one batch role to use this command.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 



        user_premium_batch_number =None 
        for role in user_roles :
            if role .id in self .PREMIUM_FB_BATCH_ROLES :
                batch_num =self .PREMIUM_FB_BATCH_ROLES [role .id ]

                if user_premium_batch_number is None or batch_num <user_premium_batch_number :
                    user_premium_batch_number =batch_num 

        if user_premium_batch_number is not None :
            pending_type ="premium"
            batch_number =user_premium_batch_number 
        else :

            user_normal_batch_number =None 
            for role in user_roles :
                if role .id in self .FB_BATCH_ROLES :
                    batch_num =self .FB_BATCH_ROLES [role .id ]

                    if user_normal_batch_number is None or batch_num <user_normal_batch_number :
                        user_normal_batch_number =batch_num 

            if user_normal_batch_number is None :
                embed =discord .Embed (
                title ="**No Batch Role Found**",
                description ="You do not have any of the required batch roles to view pending feedbacks.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 

            pending_type ="normal"
            batch_number =user_normal_batch_number 

        try :

            initial_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> Searching Pending Feedbacks...",
            description ="Please wait while we fetch the pending feedbacks.",
            color =0x000001 
            )
            message =await ctx .send (embed =initial_embed )


            conn =self .connect_to_pending (batch_number ,pending_type )
            cursor =conn .cursor ()

            cursor .execute ("SELECT * FROM pending_feedback")
            pending_feedback =cursor .fetchall ()


            if not pending_feedback :
                embed =discord .Embed (
                title ="No Pending Feedbacks",
                description ="There are currently no pending feedbacks in your batch.",
                color =0x000001 
                )
                await message .edit (embed =embed )
                conn .close ()
                return 


            feedback_chunks =[pending_feedback [i :i +20 ]for i in range (0 ,len (pending_feedback ),20 )]


            for i ,chunk in enumerate (feedback_chunks ):
                embed =discord .Embed (
                title =f"Pending Feedbacks (Batch {batch_number }, {'Premium'if pending_type =='premium'else 'Normal'}) - Page {i +1 }/{len (feedback_chunks )}",
                color =0x000001 
                )


                for feedback in chunk :
                    embed .add_field (
                    name =f"Feedback #{feedback ['vouch_number']}",
                    value =(
                    f"-# **Giver:** <@{feedback ['giver_id']}>\n"
                    f"-# **Receiver:** <@{feedback ['receiver_id']}>\n"
                    f"-# **Type:** {feedback ['type'].capitalize ()}\n"
                    f"-# **Feedback:** {feedback ['feedback']}\n"
                    f"-# **Timestamp:** {feedback ['timestamp']}\n"
                    f"-# **Feedback ID:** ```{feedback ['vouch_number']}```"
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
            await message .edit (embed =error_embed )


async def setup (bot ):
    await bot .add_cog (PendingAll (bot ))
