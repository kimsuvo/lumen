import discord 
import sqlite3 
import pytz 
import requests 
import os 
from datetime import datetime ,timedelta 
from discord .ext import commands 
from config import (
REPORT_STAFF_ROLE ,
CONFIRM_FEEDBACK_CHANNEL_ID ,
PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID ,
REJECTED_FEEDBACK_CONFIRMED_CHANNEL_ID 
)


IST =pytz .timezone ('Asia/Kolkata')

def get_feedback_db_path ():
    """
    Determines the appropriate feedback database path.
    Creates a new database file if the current one has 1,000 tables.
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

class ConP (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    class RejectedFeedbackView (discord .ui .View ):
        """A view with Confirm and Cancel buttons for rejected feedback."""

        def __init__ (self ,timeout ,ctx ,vouch_number ,pending_feedback ,db_path ,log_channel_id ,cog_instance ):
            super ().__init__ (timeout =timeout )
            self .ctx =ctx 
            self .vouch_number =vouch_number 
            self .pending_feedback =pending_feedback 
            self .db_path =db_path 
            self .log_channel_id =log_channel_id 
            self .cog_instance =cog_instance 
            self .response =None 

        @discord .ui .button (label ="CONFIRM",style =discord .ButtonStyle .success )
        async def confirm (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

            if interaction .user .id !=self .ctx .author .id :
                await interaction .response .send_message ("You are not authorized to use these buttons.",ephemeral =True )
                return 


            conn =sqlite3 .connect (self .db_path )
            cursor =conn .cursor ()
            cursor .execute ("DELETE FROM rejected_feedback WHERE vouch_number = ?",(self .vouch_number ,))
            conn .commit ()
            conn .close ()

            self .response ="confirmed"
            await interaction .response .defer ()
            self .stop ()

        @discord .ui .button (label ="CANCEL",style =discord .ButtonStyle .danger )
        async def cancel (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

            if interaction .user .id !=self .ctx .author .id :
                await interaction .response .send_message ("You are not authorized to use these buttons.",ephemeral =True )
                return 

            self .response ="cancelled"
            await interaction .response .defer ()
            self .stop ()

    @commands .command (aliases =["ConPend","conpend","conp"])
    async def ConP (self ,ctx ,vouch_number :str ):
        """
        Confirms a pending feedback based on the provided vouch number.
        The process involves searching in the following directories:
            - pendingfeedbackdatabase
            - premiumpendingfeedback
            - verificationdatabase
            - rejectedfeedbacks (table name: rejected_feedback)

        For feedback found in rejectedfeedbacks, an embed with two buttons (CONFIRM and CANCEL)
        is sent. If cancelled, the process is aborted. If confirmed, the feedback is processed.
        """

        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Approving Feedback...**",
        description =f"Approving the feedback with Vouch Number `{vouch_number }`...",
        color =0x000001 ,
        timestamp =datetime .now (IST )
        )
        confirmation_message =await ctx .send (embed =initial_embed )


        if not any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ):
            embed =discord .Embed (
            description ="You do not have the required role to use this command.",
            color =0xfbb03b 
            )
            await confirmation_message .edit (embed =embed )
            return 





        search_directories =[
        ('pendingfeedbackdatabase',CONFIRM_FEEDBACK_CHANNEL_ID ,'pending_feedback'),
        ('premiumpendingfeedback',PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID ,'pending_feedback'),
        ('verificationdatabase',CONFIRM_FEEDBACK_CHANNEL_ID ,'pending_feedback'),
        ('premiumverificationfeedback',PREMIUM_CONFIRM_FEEDBACK_CHANNEL_ID ,'pending_feedback'),
        ('rejectedfeedbacks',REJECTED_FEEDBACK_CONFIRMED_CHANNEL_ID ,'rejected_feedback')
        ]

        pending_feedback =None 
        log_channel_id =None 
        found_directory =None 
        rejected_db_path =None 


        for directory ,channel_id ,table_name in search_directories :
            os .makedirs (directory ,exist_ok =True )
            for filename in os .listdir (directory ):
                if filename .endswith ('.db'):
                    db_path =os .path .join (directory ,filename )
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()


                    cursor .execute (f"""
                        CREATE TABLE IF NOT EXISTS {table_name } (
                            vouch_number TEXT PRIMARY KEY,
                            giver_id TEXT NOT NULL,
                            receiver_id TEXT NOT NULL,
                            feedback TEXT NOT NULL,
                            timestamp TEXT NOT NULL,
                            type TEXT NOT NULL
                        )
                    """)
                    conn .commit ()
                    cursor .execute (f"SELECT * FROM {table_name } WHERE vouch_number = ?",(vouch_number ,))
                    result =cursor .fetchone ()
                    if result :
                        pending_feedback =result 
                        log_channel_id =channel_id 
                        found_directory =directory 

                        if table_name !='rejected_feedback':
                            cursor .execute (f"DELETE FROM {table_name } WHERE vouch_number = ?",(vouch_number ,))
                            conn .commit ()
                        else :

                            rejected_db_path =db_path 
                        conn .close ()
                        break 
                    conn .close ()
            if pending_feedback :
                break 


        if not pending_feedback :
            embed =discord .Embed (
            title ="**Incorrect Feedback ID**",
            description =f"No feedback found with Feedback ID `{vouch_number }`.",
            color =0x000001 
            )
            await confirmation_message .edit (embed =embed )
            return 


        vouch_number_val ,giver_id ,receiver_id ,feedback ,timestamp ,feedback_type =pending_feedback 


        if found_directory =="rejectedfeedbacks":
            prompt_embed =discord .Embed (
            title ="**Rejected Feedback Detected**",
            description =(
            f"Feedback with ID `{vouch_number }` was previously rejected.\n\n"
            "Do you want to confirm this feedback anyway?"
            ),
            color =0xff0000 ,
            timestamp =datetime .now (IST )
            )
            view =self .RejectedFeedbackView (
            timeout =60 ,
            ctx =ctx ,
            vouch_number =vouch_number ,
            pending_feedback =pending_feedback ,
            db_path =rejected_db_path ,
            log_channel_id =log_channel_id ,
            cog_instance =self 
            )
            await confirmation_message .edit (embed =prompt_embed ,view =view )


            await view .wait ()

            if view .response !="confirmed":
                cancel_embed =discord .Embed (
                title ="**Action Cancelled**",
                description ="Feedback confirmation has been cancelled.",
                color =0xFF0000 ,
                timestamp =datetime .now (IST )
                )
                await confirmation_message .edit (embed =cancel_embed ,view =None )
                return 










        await self .confirm_feedback (receiver_id ,giver_id ,feedback ,feedback_type ,timestamp )


        try :
            receiver =await self .bot .fetch_user (int (receiver_id ))
            dm_embed =discord .Embed (
            title ="**Feedback Approved**",
            description =f"<:lumen_online:1324983167538696303> Your {feedback_type .capitalize ()} feedback ID `{vouch_number }` given by <@{giver_id }> has been approved.",
            color =0x000001 
            )
            await receiver .send (embed =dm_embed )
        except discord .Forbidden :
            dm_fail_embed =discord .Embed (
            description ="Could not DM the user, but the feedback was approved.",
            color =0xFF0000 
            )
            await confirmation_message .edit (embed =dm_fail_embed )
        else :

            final_embed =discord .Embed (
            title ="**Feedback Approved**",
            description =f"<:lumen_online:1324983167538696303> Feedback for <@{receiver_id }> has been approved.",
            color =0x000001 
            )
            await confirmation_message .edit (embed =final_embed ,view =None )


        await self .update_cpinfo (ctx .author .id )


        log_channel =self .bot .get_channel (log_channel_id )
        if log_channel :
            log_embed =discord .Embed (
            title ="**Feedback Approved**",
            description ="A feedback has been approved and logged.",
            color =0x000001 
            )
            log_embed .add_field (name ="Feedback ID",value =vouch_number ,inline =False )
            log_embed .add_field (name ="Approved By",value =f"<@{ctx .author .id }>",inline =False )
            log_embed .add_field (name ="Receiver ID",value =f"<@{receiver_id }>",inline =False )
            log_embed .add_field (name ="Giver ID",value =f"<@{giver_id }>",inline =False )
            log_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
            log_embed .add_field (name ="Feedback",value =feedback ,inline =False )
            await log_channel .send (embed =log_embed )
        else :
            print (f"Error: Could not find channel with ID {log_channel_id }")

    async def update_cpinfo (self ,admin_id ):
        """
        Updates the cpinfo database with the staff's confirmation count.
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
        Updates the feedback counts for the receiver in the feedback_count databases.
        Stores databases in the 'feedbackcountdatabase' directory with up to 5000 entries each.
        Creates new databases as needed and updates existing entries if found.
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

async def setup (bot ):
    await bot .add_cog (ConP (bot ))
