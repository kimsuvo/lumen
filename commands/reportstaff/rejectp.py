import discord 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
import requests 
import os 
from discord .ui import Button ,View 

from config import (
REJECT_FEEDBACK_CHANNEL_ID ,
PREMIUM_REJECT_FEEDBACK_CHANNEL_ID ,
REPORT_STAFF_ROLE 
)


kolkata_tz =pytz .timezone ('Asia/Kolkata')


def create_db_connection (db_path ):
    return sqlite3 .connect (db_path )

class RejectP (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="rejectp",aliases =["RejectP"])
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def reject_feedback (self ,ctx ,vouch_number :str ,*,reason :str ="No reason provided"):


        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Rejecting Feedback...**",
        description =f"Rejecting the feedback with Vouch Number `{vouch_number }`.",
        color =0x000001 ,
        timestamp =datetime .now (kolkata_tz )
        )
        rejection_message =await ctx .send (embed =initial_embed )

        feedback_entry =None 
        found_conn =None 
        found_cursor =None 
        found_batch =None 
        source_category ="regular"


        directories_to_search =[
        ("pendingfeedbackdatabase","regular"),
        ("verificationdatabase","regular"),
        ("premiumpendingfeedback","premium"),
        ("premiumverificationfeedback","premium")
        ]


        for directory ,category in directories_to_search :
            if os .path .exists (directory ):
                for filename in os .listdir (directory ):
                    if filename .endswith (".db"):
                        db_path =os .path .join (directory ,filename )
                        conn =create_db_connection (db_path )
                        cursor =conn .cursor ()
                        cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
                        row =cursor .fetchone ()
                        if row :
                            feedback_entry =row 
                            found_conn =conn 
                            found_cursor =cursor 
                            source_category =category 

                            try :
                                found_batch =filename .split ("_")[-1 ].split (".")[0 ]
                            except Exception :
                                found_batch ="Unknown"
                            break 
                        else :
                            conn .close ()
                if feedback_entry :
                    break 


        if not feedback_entry :
            embed =discord .Embed (
            title ="**Incorrect Feedback ID**",
            description =f"No feedback found with Feedback ID `{vouch_number }`.",
            color =0x000001 ,
            timestamp =datetime .now (kolkata_tz )
            )
            await rejection_message .edit (embed =embed )
            return 


        found_cursor .execute ("DELETE FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
        found_conn .commit ()


        rejected_dir ="rejectedfeedbacks"
        if not os .path .exists (rejected_dir ):
            os .makedirs (rejected_dir )

        def get_rejected_db_path ():

            db_files =[f for f in os .listdir (rejected_dir )if f .startswith ("rejected_fb_")and f .endswith (".db")]
            if not db_files :

                return os .path .join (rejected_dir ,"rejected_fb_1.db")

            db_files .sort (key =lambda x :int (x .split ("_")[-1 ].split (".")[0 ]))
            latest_db =db_files [-1 ]
            latest_db_path =os .path .join (rejected_dir ,latest_db )

            conn_latest =sqlite3 .connect (latest_db_path )
            cursor_latest =conn_latest .cursor ()
            cursor_latest .execute ("""
                CREATE TABLE IF NOT EXISTS rejected_feedback (
                    vouch_number TEXT PRIMARY KEY,
                    giver_id TEXT NOT NULL,
                    receiver_id TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            """)

            conn_latest .commit ()
            cursor_latest .execute ("SELECT COUNT(*) FROM rejected_feedback")
            count =cursor_latest .fetchone ()[0 ]
            conn_latest .close ()
            if count <50000 :
                return latest_db_path 
            else :

                next_number =int (latest_db .split ("_")[-1 ].split (".")[0 ])+1 
                return os .path .join (rejected_dir ,f"rejected_fb_{next_number }.db")

        rejected_db_path =get_rejected_db_path ()
        conn_rejected =sqlite3 .connect (rejected_db_path )
        cursor_rejected =conn_rejected .cursor ()
        cursor_rejected .execute ("""
            CREATE TABLE IF NOT EXISTS rejected_feedback (
                vouch_number TEXT PRIMARY KEY,
                giver_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                feedback TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)

        conn_rejected .commit ()

        timestamp_str =datetime .now (kolkata_tz ).strftime ("%Y-%m-%d %H:%M:%S")
        cursor_rejected .execute ("""
            INSERT INTO rejected_feedback (vouch_number, giver_id, receiver_id, feedback, timestamp, type)
            VALUES (?, ?, ?, ?, ?, ?)
        """,(vouch_number ,feedback_entry [1 ],feedback_entry [2 ],feedback_entry [3 ],timestamp_str ,feedback_entry [5 ]))


        conn_rejected .commit ()




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
            description =(
            f"Feedback given by <@{giver_id }> for you has been rejected.\n"
            f"Feedback ID: `{vouch_number }`\n"
            f"If you think this is a mistake, please open a Support Ticket at **[Lumen Support Server](https://discord.gg/lumenreport)**.\n"
            f"**Reason:** `{reason }`"
            ),
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
        description =(
        f"Feedback with Vouch Number `{vouch_number }` has been successfully rejected"
        +(f" and removed from Batch `{found_batch }`."if found_batch else ".")
        +f"\n**Reason:** `{reason }`"
        ),
        color =0x000001 ,
        timestamp =datetime .now (kolkata_tz )
        )
        await rejection_message .edit (embed =embed )


        found_conn .close ()


        if source_category =="regular":
            log_channel_id =REJECT_FEEDBACK_CHANNEL_ID 
        else :
            log_channel_id =PREMIUM_REJECT_FEEDBACK_CHANNEL_ID 

        channel =ctx .guild .get_channel (log_channel_id )
        if channel :
            log_embed =discord .Embed (
            title ="Feedback Rejected",
            description =(
            f"Feedback **#{vouch_number }** has been rejected.\n"
            f"**Giver:** <@{giver_id }>\n"
            f"**Receiver:** <@{receiver_id }>\n"
            f"**Rejected By:** <@{ctx .author .id }>\n"
            f"**Category:** `{source_category }`"
            ),
            color =0x000001 ,
            timestamp =datetime .now (kolkata_tz )
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


async def setup (bot ):
    await bot .add_cog (RejectP (bot ))
