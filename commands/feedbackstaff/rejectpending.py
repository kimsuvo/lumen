import discord 
from discord .ext import commands 
from discord .ui import Button ,View 
import sqlite3 
from datetime import datetime 
import pytz 
import os 

from config import (
REJECT_FEEDBACK_CHANNEL_ID ,
PREMIUM_REJECT_FEEDBACK_CHANNEL_ID ,
FEEDBACK_ADMIN_ROLE ,
FB_BATCH_1 ,
FB_BATCH_2 ,
FB_BATCH_3 ,
FB_BATCH_4 ,
FB_BATCH_5 ,
FB_BATCH_6 ,
FB_BATCH_7 ,
FB_BATCH_8 ,
FB_BATCH_9 ,
FB_BATCH_10 ,
PREMIUM_FB_BATCH_1 ,
PREMIUM_FB_BATCH_2 ,
PREMIUM_FB_BATCH_3 ,
PREMIUM_FB_BATCH_4 ,
PREMIUM_FB_BATCH_5 ,
PREMIUM_FB_BATCH_6 ,
PREMIUM_FB_BATCH_7 ,
PREMIUM_FB_BATCH_8 ,
PREMIUM_FB_BATCH_9 ,
PREMIUM_FB_BATCH_10 
)


kolkata_tz =pytz .timezone ('Asia/Kolkata')


def create_db_connection (db_path ):
    return sqlite3 .connect (db_path )

class RejectPending (commands .Cog ):
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

    @commands .command (name ="rejectpending",aliases =["rp"])
    async def reject_feedback (self ,ctx ,vouch_number :str ,*,reason :str ):

        if not reason .strip ():
            embed =discord .Embed (
            title ="Missing Reason",
            description ="You must provide a reason for rejecting the feedback.",
            color =0xFF0000 ,
            timestamp =datetime .now (kolkata_tz )
            )
            await ctx .send (embed =embed )
            return 


        user_role_ids =[role .id for role in ctx .author .roles ]
        if not any (role_id in FEEDBACK_ADMIN_ROLE for role_id in user_role_ids ):
            embed =discord .Embed (
            title ="**Permission Required**",
            description ="You do not have the required FEEDBACK_ADMIN_ROLE to use this command.",
            color =discord .Color .red (),
            timestamp =datetime .now (kolkata_tz )
            )
            await ctx .send (embed =embed )
            return 




        all_batch_role_ids =(
        [role for roles in self .premium_batch_roles .values ()for role in roles ]+
        [role for roles in self .standard_batch_roles .values ()for role in roles ]
        )
        user_batch_roles =[role_id for role_id in user_role_ids if role_id in all_batch_role_ids ]
        if len (user_batch_roles )>1 :
            embed =discord .Embed (
            title ="**Multiple Batch Roles Detected**",
            description ="You have more than one batch role assigned. Please contact an administrator.",
            color =discord .Color .red (),
            timestamp =datetime .now (kolkata_tz )
            )
            await ctx .send (embed =embed )
            return 



        batch_number =None 
        pending_db =None 
        verification_db =None 

        is_premium =False 

        for num ,role_ids in self .premium_batch_roles .items ():
            if any (role in user_role_ids for role in role_ids ):
                batch_number =num 
                is_premium =True 
                pending_db =os .path .join ("premiumpendingfeedback",f"premium_pending_fb_{batch_number }.db")
                verification_db =os .path .join ("premiumverificationfeedback",f"premium_verification_fb_{batch_number }.db")
                break 


        if batch_number is None :
            for num ,role_ids in self .standard_batch_roles .items ():
                if any (role in user_role_ids for role in role_ids ):
                    batch_number =num 
                    pending_db =os .path .join ("pendingfeedbackdatabase",f"pending_fb_{batch_number }.db")
                    verification_db =os .path .join ("verificationdatabase",f"verification_fb_{batch_number }.db")
                    break 



        if batch_number is None :
            embed =discord .Embed (
            title ="**Batch Role Required**",
            description ="You do not have any valid FB_BATCH_x or PREMIUM_FB_BATCH_x role assigned. Please contact an administrator.",
            color =discord .Color .red (),
            timestamp =datetime .now (kolkata_tz )
            )
            await ctx .send (embed =embed )
            return 


        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Rejecting Feedback...**",
        description =f"Rejecting the feedback with Vouch Number `{vouch_number }` from Batch `{batch_number }`.",
        color =0x000001 ,
        timestamp =datetime .now (kolkata_tz )
        )
        rejection_message =await ctx .send (embed =initial_embed )


        conn =create_db_connection (pending_db )
        cursor =conn .cursor ()
        cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
        feedback_entry =cursor .fetchone ()


        if not feedback_entry :
            conn .close ()
            conn =create_db_connection (verification_db )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
            feedback_entry =cursor .fetchone ()

        if not feedback_entry :
            embed =discord .Embed (
            title ="**Incorrect Feedback ID**",
            description =f"No feedback found with Feedback ID `{vouch_number }` in Batch `{batch_number }`.",
            color =0x000001 ,
            )
            await rejection_message .edit (embed =embed )
            conn .close ()
            return 



        cursor .execute ("DELETE FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
        conn .commit ()


        try :
            self .store_rejected_feedback (vouch_number ,feedback_entry ,reason ,ctx .author .id ,batch_number )
        except Exception as e :
            print (f"Error storing rejected feedback: {e }")


        try :
            giver_id =int (feedback_entry [1 ])
            receiver_id =int (feedback_entry [2 ])
            feedback_text =feedback_entry [3 ]

            giver =await self .bot .fetch_user (giver_id )
            notify_embed =discord .Embed (
            title ="**Feedback Rejected**",
            description =(f"<:lumen_dnd:1324983165554524252> Your feedback for <@{receiver_id }> has been rejected.\n-# **Reason:** `{reason }`"),
            color =0xFF0000 ,
            timestamp =datetime .now (kolkata_tz )
            )
            notify_embed .add_field (name ="Feedback",value =feedback_text ,inline =False )
            await giver .send (embed =notify_embed )
        except discord .Forbidden :
            await ctx .send (f"Could not notify <@{giver_id }> about the feedback rejection (DMs are closed).")


        try :
            receiver =await self .bot .fetch_user (receiver_id )
            notify_embed_receiver =discord .Embed (
            title ="**Feedback Notification System**",
            description =(f"Feedback given by <@{giver_id }> for you has been rejected. "
            f"The Feedback ID is `{vouch_number }`.\nIf you think this is a mistake, "
            "you can open a Support Ticket at **[Lumen Support Server](https://discord.gg/lumenreport)**.\n"
            f"**Reason:** `{reason }`"),
            color =0xFF0000 ,
            timestamp =datetime .now (kolkata_tz )
            )
            support_button =Button (
            label ="Lumen Support Server",
            url ="https://discord.gg/lumenreport"
            )
            view =View ()
            view .add_item (support_button )
            await receiver .send (embed =notify_embed_receiver ,view =view )
        except discord .Forbidden :
            await ctx .send (f"Could not notify <@{receiver_id }> about the feedback rejection (DMs are closed).")


        embed =discord .Embed (
        title ="**Feedback Rejected**",
        description =(f"Feedback with Vouch Number `{vouch_number }` has been successfully rejected and removed from Batch `{batch_number }`.\n"
        f"**Reason:** `{reason }`"),
        color =0x000001 ,
        timestamp =datetime .now (kolkata_tz )
        )
        await rejection_message .edit (embed =embed )
        conn .close ()


        channel_id =PREMIUM_REJECT_FEEDBACK_CHANNEL_ID if is_premium else REJECT_FEEDBACK_CHANNEL_ID 
        channel =ctx .guild .get_channel (channel_id )
        if channel :
            log_embed =discord .Embed (
            title ="Feedback Rejected",
            description =(f"Feedback **#{vouch_number }** has been rejected.\n"
            f"**Giver:** <@{giver_id }>\n"
            f"**Receiver:** <@{receiver_id }>\n"
            f"**Batch:** {batch_number }\n"
            f"**Rejected By:** <@{ctx .author .id }>"),
            color =0x000001 
            )
            await channel .send (embed =log_embed )
        else :
            print ("Error: Rejection feedback channel not found.")


        await self .update_cpinfo (ctx .author .id )

    async def update_cpinfo (self ,admin_id ):
        cpinfo_path =os .path .join ('infodatabase','cpinfo.db')
        cpinfo_conn =sqlite3 .connect (cpinfo_path )
        cpinfo_cursor =cpinfo_conn .cursor ()
        cpinfo_cursor .execute ("""
            CREATE TABLE IF NOT EXISTS cpinfo (
                user_id TEXT PRIMARY KEY,
                confirm_count INTEGER DEFAULT 0,
                reject_count INTEGER DEFAULT 0,
                verify_count INTEGER DEFAULT 0              
            )
        """)
        cpinfo_cursor .execute ("SELECT reject_count FROM cpinfo WHERE user_id = ?",(str (admin_id ),))
        result =cpinfo_cursor .fetchone ()
        if result :
            new_count =result [0 ]+1 
            cpinfo_cursor .execute ("""
                UPDATE cpinfo
                SET reject_count = ?
                WHERE user_id = ?
            """,(new_count ,str (admin_id )))
        else :
            cpinfo_cursor .execute ("""
                INSERT INTO cpinfo (user_id, reject_count)
                VALUES (?, ?)
            """,(str (admin_id ),1 ))
        cpinfo_conn .commit ()
        cpinfo_conn .close ()

    def store_rejected_feedback (self ,original_vouch ,feedback_entry ,reason ,rejected_by ,batch_number ):
        os .makedirs ("rejectedfeedbacks",exist_ok =True )
        db_index =1 
        inserted =False 
        while not inserted :
            db_path =os .path .join ("rejectedfeedbacks",f"rejected_fb_{db_index }.db")
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("""
                CREATE TABLE IF NOT EXISTS rejected_feedback (
                    vouch_number TEXT PRIMARY KEY,
                    giver_id TEXT NOT NULL,
                    receiver_id TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            """)
            conn .commit ()
            cursor .execute ("SELECT COUNT(*) FROM rejected_feedback")
            count =cursor .fetchone ()[0 ]
            if count <50000 :
                cursor .execute ("SELECT 1 FROM rejected_feedback WHERE vouch_number = ?",(original_vouch ,))
                exists =cursor .fetchone ()
                if exists :
                    conn .close ()
                    db_index +=1 
                    continue 
                timestamp =datetime .now (kolkata_tz ).strftime ("%Y-%m-%d %H:%M:%S")
                cursor .execute ("""
                    INSERT INTO rejected_feedback 
                    (vouch_number, giver_id, receiver_id, feedback, timestamp, type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,(original_vouch ,feedback_entry [1 ],feedback_entry [2 ],feedback_entry [3 ],timestamp ,feedback_entry [5 ]))
                conn .commit ()
                inserted =True 
            conn .close ()
            if not inserted :
                db_index +=1 


async def setup (bot ):
    await bot .add_cog (RejectPending (bot ))
