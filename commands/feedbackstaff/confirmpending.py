import discord 
import sqlite3 
import pytz 
import requests 
import os 
from datetime import datetime ,timedelta 
from discord .ext import commands 
from config import (
FEEDBACK_ADMIN_ROLE ,
MANAGEMENT_ROLE_ID ,
REPORT_STAFF_ROLE ,
CONFIRM_FEEDBACK_CHANNEL_ID ,
PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID ,
FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ,
PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,
PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 
)


IST =pytz .timezone ('Asia/Kolkata')

def get_feedback_db_path ():
    """
    Determines the appropriate feedback database path.
    Creates a new database file if the current one has 1000 tables.
    """
    db_dir ='feedbackdatabase'
    if not os .path .exists (db_dir ):
        os .makedirs (db_dir )

    db_number =1 
    while True :
        db_path =os .path .join (db_dir ,f'feedback_{db_number }.db')
        if not os .path .exists (db_path ):
            return db_path 


        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT count(*) FROM sqlite_master WHERE type='table'")
        table_count =cursor .fetchone ()[0 ]
        conn .close ()

        if table_count <1000 :
            return db_path 

        db_number +=1 


class ConfirmPending (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .standard_batch_roles ={}
        for batch_number ,roles in enumerate (
        [FB_BATCH_1 ,FB_BATCH_2 ,FB_BATCH_3 ,FB_BATCH_4 ,FB_BATCH_5 ,
        FB_BATCH_6 ,FB_BATCH_7 ,FB_BATCH_8 ,FB_BATCH_9 ,FB_BATCH_10 ],
        start =1 
        ):
            for role_id in roles :
                self .standard_batch_roles [role_id ]=batch_number 

        self .premium_batch_roles ={}
        for batch_number ,roles in enumerate (
        [PREMIUM_FB_BATCH_1 ,PREMIUM_FB_BATCH_2 ,PREMIUM_FB_BATCH_3 ,PREMIUM_FB_BATCH_4 ,PREMIUM_FB_BATCH_5 ,
        PREMIUM_FB_BATCH_6 ,PREMIUM_FB_BATCH_7 ,PREMIUM_FB_BATCH_8 ,PREMIUM_FB_BATCH_9 ,PREMIUM_FB_BATCH_10 ],
        start =1 
        ):
            for role_id in roles :
                self .premium_batch_roles [role_id ]=batch_number 



    @commands .command (aliases =["cp"])
    async def confirmpending (self ,ctx ,vouch_number :str ):
        """
        Confirms a pending feedback based on the provided vouch number.
        This version improves the batch role checking by ensuring that the user
        has exactly one valid batch role, whether standard or premium.
        """

        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Approving Feedback...**",
        description =f"Approving the feedback with Vouch Number `{vouch_number }`...",
        color =0x000001 ,
        timestamp =datetime .now (IST )
        )
        confirmation_message =await ctx .send (embed =initial_embed )


        if not any (role .id in FEEDBACK_ADMIN_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            description ="You do not have the required role to use this command.",
            color =0xfbb03b 
            )
            await confirmation_message .edit (embed =embed )
            return 



        user_role_ids ={role .id for role in ctx .author .roles }
        valid_batch_role_ids =set (self .standard_batch_roles .keys ())|set (self .premium_batch_roles .keys ())
        user_batch_roles =user_role_ids .intersection (valid_batch_role_ids )



        if len (user_batch_roles )!=1 :
            embed =discord .Embed (
            title ="**Batch Role Issue Detected**",
            description ="You must have exactly one batch role (standard or premium) assigned. "
            "If you believe this is an error, please contact an administrator.",
            color =0xff0000 
            )
            await confirmation_message .edit (embed =embed )
            return 



        is_premium =False 
        user_batch_role =next (iter (user_batch_roles ))
        if user_batch_role in self .premium_batch_roles :
            batch_number =self .premium_batch_roles [user_batch_role ]
            is_premium =True 
        elif user_batch_role in self .standard_batch_roles :
            batch_number =self .standard_batch_roles [user_batch_role ]
        else :
            embed =discord .Embed (
            description ="Could not determine your batch role. Please contact an administrator.",
            color =0xfbb03b 
            )
            await confirmation_message .edit (embed =embed )
            return 



        if is_premium :
            pending_db_dir ='premiumpendingfeedback'
            verification_db_dir ='premiumverificationfeedback'
            pending_db_path =os .path .join (pending_db_dir ,f'premium_pending_fb_{batch_number }.db')
            verification_db_path =os .path .join (verification_db_dir ,f'premium_verification_fb_{batch_number }.db')
        else :
            pending_db_dir ='pendingfeedbackdatabase'
            verification_db_dir ='verificationdatabase'
            pending_db_path =os .path .join (pending_db_dir ,f'pending_fb_{batch_number }.db')
            verification_db_path =os .path .join (verification_db_dir ,f'verification_fb_{batch_number }.db')


        os .makedirs (pending_db_dir ,exist_ok =True )
        os .makedirs (verification_db_dir ,exist_ok =True )


        pending_feedback_conn =sqlite3 .connect (pending_db_path )
        pending_cursor =pending_feedback_conn .cursor ()
        pending_cursor .execute (""" 
            CREATE TABLE IF NOT EXISTS pending_feedback (
                vouch_number TEXT PRIMARY KEY,
                giver_id TEXT,
                receiver_id TEXT,
                feedback TEXT,
                timestamp TEXT,
                feedback_type TEXT
            )
        """)
        pending_feedback_conn .commit ()


        pending_cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
        pending_feedback =pending_cursor .fetchone ()
        source_db ='pending'


        if not pending_feedback :
            verification_conn =sqlite3 .connect (verification_db_path )
            verification_cursor =verification_conn .cursor ()
            verification_cursor .execute (""" 
                CREATE TABLE IF NOT EXISTS pending_feedback (
                    vouch_number TEXT PRIMARY KEY,
                    giver_id TEXT,
                    receiver_id TEXT,
                    feedback TEXT,
                    timestamp TEXT,
                    feedback_type TEXT
                )
            """)
            verification_conn .commit ()
            verification_cursor .execute ("SELECT * FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
            pending_feedback =verification_cursor .fetchone ()

            if pending_feedback :

                verification_cursor .execute ("DELETE FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
                verification_conn .commit ()
                source_db ='verification'
            verification_conn .close ()


        if not pending_feedback :
            rejected_db_dir ='rejectedfeedbacks'
            if os .path .exists (rejected_db_dir ):
                for filename in os .listdir (rejected_db_dir ):
                    if filename .startswith ('rejected_fb_')and filename .endswith ('.db'):
                        rejected_db_path =os .path .join (rejected_db_dir ,filename )
                        rejected_conn =sqlite3 .connect (rejected_db_path )
                        rejected_cursor =rejected_conn .cursor ()
                        rejected_cursor .execute ("SELECT * FROM rejected_feedback WHERE vouch_number = ?",(vouch_number ,))
                        pending_feedback =rejected_cursor .fetchone ()
                        if pending_feedback :
                            source_db ='rejected'
                            rejected_conn .close ()
                            break 
                        rejected_conn .close ()


        if not pending_feedback :
            embed =discord .Embed (
            title ="**Incorrect Feedback ID**",
            description =f"No feedback found with Feedback ID `{vouch_number }` in Batch `{batch_number }`.",
            color =0x000001 
            )
            await confirmation_message .edit (embed =embed )
            pending_feedback_conn .close ()
            return 


        if source_db =='rejected':

            class PingAdminsView (discord .ui .View ):
                def __init__ (self ,*,timeout =180 ):
                    super ().__init__ (timeout =timeout )

                @discord .ui .button (label ="Ping Admins",style =discord .ButtonStyle .primary )
                async def ping_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

                    button .disabled =True 
                    await interaction .response .edit_message (view =self )

                    management_role =ctx .guild .get_role (MANAGEMENT_ROLE_ID )
                    report_staff_role =ctx .guild .get_role (REPORT_STAFF_ROLE )
                    ping_message =f"{management_role .mention } {report_staff_role .mention } A rejected feedback has been attempted for confirmation."
                    await ctx .send (ping_message )

            view =PingAdminsView ()
            embed =discord .Embed (
            title ="**Rejected Feedback Detected**",
            description =(
            "Your feedback has been **rejected** by the staff.\n\n"
            "If you believe this was a mistake, contact the **Report Staff** or **Server Management** for clarification.\n\n"
            "**Important:**\n"
            "- Do not misuse the ping feature.\n"
            "- Unnecessary pings may result in strict action.\n"
            "- Use it only when absolutely necessary and with valid reasoning."
            ),
            color =0xFF0000 ,
            timestamp =datetime .now (IST )
            )
            await confirmation_message .edit (embed =embed ,view =view )
            pending_feedback_conn .close ()
            return 


        vouch_number ,giver_id ,receiver_id ,feedback ,timestamp ,feedback_type =pending_feedback 


        if source_db =='pending':
            pending_cursor .execute ("DELETE FROM pending_feedback WHERE vouch_number = ?",(vouch_number ,))
            pending_feedback_conn .commit ()
        pending_feedback_conn .close ()


        await self .confirm_feedback (receiver_id ,giver_id ,feedback ,feedback_type ,timestamp )


        try :
            receiver =await self .bot .fetch_user (int (receiver_id ))
            embed =discord .Embed (
            title ="**Feedback Approved**",
            description =f"<:lumen_online:1324983167538696303> Your {feedback_type .capitalize ()} feedback ID `{vouch_number }` given by <@{giver_id }> has been approved.",
            color =0x000001 
            )
            await receiver .send (embed =embed )
        except discord .Forbidden :
            embed =discord .Embed (
            description ="Could not DM the user, but the feedback was approved.",
            color =0xFF0000 
            )
            await confirmation_message .edit (embed =embed )
        else :

            embed =discord .Embed (
            title ="**Feedback Approved**",
            description =f"<:lumen_online:1324983167538696303> Feedback for <@{receiver_id }> has been approved.",
            color =0x000001 
            )
            await confirmation_message .edit (embed =embed )


        await self .update_cpinfo (ctx .author .id )


        await self .send_log_to_webhook (
        vouch_number ,giver_id ,receiver_id ,feedback ,feedback_type ,timestamp ,ctx .author .id ,is_premium 
        )

    async def update_cpinfo (self ,admin_id ):
        """
        Updates the cpinfo database with the admin's confirmation count.
        """
        cpinfo_db_path ='infodatabase/cpinfo.db'
        cpinfo_dir =os .path .dirname (cpinfo_db_path )
        if not os .path .exists (cpinfo_dir ):
            os .makedirs (cpinfo_dir )

        cpinfo_conn =sqlite3 .connect (cpinfo_db_path )
        cpinfo_cursor =cpinfo_conn .cursor ()


        cpinfo_cursor .execute ("""
            CREATE TABLE IF NOT EXISTS cpinfo (
                user_id TEXT PRIMARY KEY,
                confirm_count INTEGER DEFAULT 0,
                reject_count INTEGER DEFAULT 0,
                verify_count INTEGER DEFAULT 0              
            )
        """)


        cpinfo_cursor .execute ("SELECT confirm_count FROM cpinfo WHERE user_id = ?",(admin_id ,))
        result =cpinfo_cursor .fetchone ()

        if result :

            new_count =result [0 ]+1 
            cpinfo_cursor .execute ("""
                UPDATE cpinfo
                SET confirm_count = ?
                WHERE user_id = ?
            """,(new_count ,admin_id ))
        else :

            cpinfo_cursor .execute ("""
                INSERT INTO cpinfo (user_id, confirm_count)
                VALUES (?, ?)
            """,(admin_id ,1 ))

        cpinfo_conn .commit ()
        cpinfo_conn .close ()

    async def confirm_feedback (self ,receiver_id ,giver_id ,feedback ,feedback_type ,timestamp ):
        """
        Stores the confirmed feedback in the appropriate feedback database.
        Ensures that each feedback database does not exceed 1,000 tables.
        """
        feedback_db_path =get_feedback_db_path ()
        feedback_conn =sqlite3 .connect (feedback_db_path )
        feedback_cursor =feedback_conn .cursor ()


        table_name =f"feedback_{receiver_id }"
        feedback_cursor .execute (f"""
            CREATE TABLE IF NOT EXISTS {table_name } (
                giver_id TEXT,
                receiver_id TEXT,
                feedback TEXT,
                feedback_type TEXT,
                timestamp TEXT
            )
        """)


        feedback_cursor .execute (f"""
            INSERT INTO {table_name } (giver_id, receiver_id, feedback, feedback_type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,(giver_id ,receiver_id ,feedback ,feedback_type ,timestamp ))


        feedback_cursor .execute (f"SELECT COUNT(*) FROM {table_name }")
        row_count =feedback_cursor .fetchone ()[0 ]
        if row_count >30000 :
            rows_to_remove =row_count -30000 
            feedback_cursor .execute (f"""
                DELETE FROM {table_name }
                WHERE rowid IN (
                    SELECT rowid FROM {table_name }
                    ORDER BY datetime(timestamp) ASC
                    LIMIT ?
                )
            """,(rows_to_remove ,))

        feedback_conn .commit ()
        feedback_conn .close ()


        await self .update_feedback_counts (receiver_id ,feedback_type )

    async def update_feedback_counts (self ,receiver_id ,feedback_type ):
        """
        Updates the feedback counts for the receiver in the feedback count databases.
        Creates new databases as needed, each holding up to 5000 entries.
        """
        feedback_count_dir ='feedbackcountdatabase'
        os .makedirs (feedback_count_dir ,exist_ok =True )

        def get_sorted_db_files ():
            db_files =[]
            for filename in os .listdir (feedback_count_dir ):
                if filename .startswith ('fb_count_')and filename .endswith ('.db'):
                    parts =filename .rstrip ('.db').split ('_')
                    if len (parts )==3 and parts [0 ]=='fb'and parts [1 ]=='count':
                        try :
                            number =int (parts [2 ])
                            db_files .append ((number ,os .path .join (feedback_count_dir ,filename )))
                        except ValueError :
                            continue 
            db_files .sort (key =lambda x :x [0 ])
            return [path for _ ,path in db_files ]

        db_files =get_sorted_db_files ()
        if not db_files :
            first_db =os .path .join (feedback_count_dir ,'fb_count_1.db')
            db_files .append (first_db )

        user_found =False 
        for db_path in db_files :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute (""" 
                CREATE TABLE IF NOT EXISTS feedback_count (
                    receiver_id TEXT PRIMARY KEY,
                    total_feedback_count INTEGER,
                    positive_feedback_count INTEGER,
                    negative_feedback_count INTEGER
                )
            """)
            cursor .execute ("SELECT total_feedback_count, positive_feedback_count, negative_feedback_count FROM feedback_count WHERE receiver_id = ?",(receiver_id ,))
            result =cursor .fetchone ()
            if result :
                total ,positive ,negative =result 
                total +=1 
                if feedback_type .lower ()=="positive":
                    positive +=1 
                else :
                    negative +=1 
                cursor .execute ("""
                    UPDATE feedback_count
                    SET total_feedback_count = ?, positive_feedback_count = ?, negative_feedback_count = ?
                    WHERE receiver_id = ?
                """,(total ,positive ,negative ,receiver_id ))
                conn .commit ()
                conn .close ()
                user_found =True 
                break 
            conn .close ()

        if not user_found :
            target_db =None 
            for db_path in db_files :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT COUNT(*) FROM feedback_count")
                count =cursor .fetchone ()[0 ]
                conn .close ()
                if count <5000 :
                    target_db =db_path 
                    break 
            if not target_db :
                last_db_number =1 
                if db_files :
                    last_db =db_files [-1 ]
                    try :
                        last_number =int (os .path .splitext (os .path .basename (last_db ))[0 ].split ('_')[-1 ])
                        last_db_number =last_number +1 
                    except (IndexError ,ValueError ):
                        last_db_number =len (db_files )+1 
                target_db =os .path .join (feedback_count_dir ,f'fb_count_{last_db_number }.db')
                db_files .append (target_db )
            conn =sqlite3 .connect (target_db )
            cursor =conn .cursor ()
            cursor .execute (""" 
                CREATE TABLE IF NOT EXISTS feedback_count (
                    receiver_id TEXT PRIMARY KEY,
                    total_feedback_count INTEGER,
                    positive_feedback_count INTEGER,
                    negative_feedback_count INTEGER
                )
            """)
            total =1 
            positive =1 if feedback_type .lower ()=="positive"else 0 
            negative =1 if feedback_type .lower ()=="negative"else 0 
            cursor .execute ("""
                INSERT INTO feedback_count (receiver_id, total_feedback_count, positive_feedback_count, negative_feedback_count)
                VALUES (?, ?, ?, ?)
            """,(receiver_id ,total ,positive ,negative ))
            conn .commit ()
            conn .close ()

    async def send_log_to_webhook (self ,vouch_number ,giver_id ,receiver_id ,feedback ,feedback_type ,timestamp ,admin_id ,is_premium ):
        """
        Sends a log of the approved feedback to the designated channel.
        If the feedback is premium, it uses PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID; otherwise, CONFIRM_FEEDBACK_CHANNEL_ID.
        """
        log_embed =discord .Embed (
        title ="**Feedback Approved**",
        description ="A feedback has been approved and logged.",
        color =0x000001 ,
        timestamp =datetime .now (IST )
        )
        log_embed .add_field (name ="Feedback ID",value =vouch_number ,inline =False )
        log_embed .add_field (name ="Approved By",value =f"<@{admin_id }>",inline =False )
        log_embed .add_field (name ="Receiver ID",value =f"<@{receiver_id }>",inline =False )
        log_embed .add_field (name ="Giver ID",value =f"<@{giver_id }>",inline =False )
        log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
        log_embed .add_field (name ="Feedback",value =feedback ,inline =False )

        channel_id =PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID if is_premium else CONFIRM_FEEDBACK_CHANNEL_ID 
        channel =self .bot .get_channel (channel_id )
        if channel :
            await channel .send (embed =log_embed )



async def setup (bot ):
    await bot .add_cog (ConfirmPending (bot ))
