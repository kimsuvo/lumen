import discord 
from discord .ext import commands 
import sqlite3 
import os 
from datetime import datetime 
from config import MANAGEMENT_ROLE_ID 

class PendingFeedbackAll (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 


        self .NORMAL_DB_DIR =os .path .join ("pendingfeedbackdatabase")
        self .PREMIUM_DB_DIR =os .path .join ("premiumpendingfeedback")

        os .makedirs (self .NORMAL_DB_DIR ,exist_ok =True )
        os .makedirs (self .PREMIUM_DB_DIR ,exist_ok =True )

    def connect_to_pending (self ,db_path ):
        """
        Connect to the pending feedback database at the given db_path.
        This will also create the table if it does not exist.
        """
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

    def fetch_feedbacks_from_db (self ,db_path ,is_premium :bool ):
        """
        Connects to a given database file and fetches all pending feedback records.
        Adds an extra key 'premium' with value 'Yes' if is_premium is True, otherwise 'No'.
        Returns a list of dictionaries.
        """
        feedbacks =[]
        try :
            conn =self .connect_to_pending (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM pending_feedback")
            rows =cursor .fetchall ()
            for row in rows :
                entry =dict (row )
                entry ["premium"]="Yes"if is_premium else "No"
                feedbacks .append (entry )
            conn .close ()
        except Exception as e :
            print (f"Error reading database {db_path }: {e }")
        return feedbacks 



    @commands .command ()
    async def pendingfeedbackall (self ,ctx ,db_type :str =None ):
        """
        Fetch all pending feedbacks from one or both directories and send them as .txt file(s).

        Usage:
          +pendingfeedbackall             -> Fetches from both normal and premium directories.
          +pendingfeedbackall premium     -> Fetches only from the premium directory.
          +pendingfeedbackall normal      -> Fetches only from the normal directory.
        """

        if not any (role .id in MANAGEMENT_ROLE_ID for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="**Permission Required**",
            description ="You do not have the required permissions to use this command.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 



        loading_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Fetching Pending Feedbacks...**",
        description ="Please wait while we gather all pending feedbacks.",
        color =0x000001 
        )
        message =await ctx .send (embed =loading_embed )

        try :
            feedbacks =[]


            db_type_chosen =None 
            if db_type is None :

                db_type_chosen ="both"
            elif db_type .lower ()in ("premium","normal"):
                db_type_chosen =db_type .lower ()
            else :
                error_embed =discord .Embed (
                title ="Error",
                description ="Invalid argument. Use no argument, `premium`, or `normal`.",
                color =discord .Color .red ()
                )
                await message .edit (embed =error_embed )
                return 


            def scan_directory (directory ,is_premium :bool ):
                collected =[]
                for filename in os .listdir (directory ):
                    if filename .endswith (".db"):
                        db_path =os .path .join (directory ,filename )
                        collected .extend (self .fetch_feedbacks_from_db (db_path ,is_premium ))
                return collected 

            if db_type_chosen in ("both","normal"):
                normal_feedbacks =scan_directory (self .NORMAL_DB_DIR ,is_premium =False )
                feedbacks .extend (normal_feedbacks )

            if db_type_chosen in ("both","premium"):
                premium_feedbacks =scan_directory (self .PREMIUM_DB_DIR ,is_premium =True )
                feedbacks .extend (premium_feedbacks )


            if not feedbacks :
                no_feedback_embed =discord .Embed (
                title ="<:lumen_online:1324983167538696303> **No Pending Feedbacks**",
                description ="There are currently no pending feedbacks in the selected database(s).",
                color =0x000001 
                )
                await message .edit (embed =no_feedback_embed )
                return 


            current_time =datetime .now ().strftime ("%d/%m/%Y %I:%M %p IST")
            header =(
            "PENDING FEEDBACK LIST\n"
            f"REQUESTED BY: {ctx .author }\n"
            f"TIMESTAMP: {current_time }\n\n"
            )


            feedback_entries =[]
            for fb in feedbacks :
                entry =(
                f"Feedback ID: {fb .get ('vouch_number','N/A')}\n"
                f"Giver ID: {fb .get ('giver_id','N/A')}\n"
                f"Receiver ID: {fb .get ('receiver_id','N/A')}\n"
                f"Feedback: {fb .get ('feedback','N/A')}\n"
                f"Feedback Type: {fb .get ('type','N/A').lower ()}\n"
                f"Timestamp: {fb .get ('timestamp','N/A')}\n"
                f"Premium: {fb .get ('premium','No')}\n"
                "--------------------------------------------------\n"
                )
                feedback_entries .append (entry )


            chunk_size =5000 
            files_to_send =[]
            for i in range (0 ,len (feedback_entries ),chunk_size ):
                chunk_entries =feedback_entries [i :i +chunk_size ]
                file_content =header +"\n".join (chunk_entries )
                file_name =f"pending_feedbacks_{i //chunk_size +1 }.txt"
                with open (file_name ,"w",encoding ="utf-8")as f :
                    f .write (file_content )
                files_to_send .append (file_name )


            embed =discord .Embed (
            title ="Pending Feedbacks",
            description ="Attached are the pending feedback list file(s).",
            color =0x000001 
            )


            for file_name in files_to_send :
                discord_file =discord .File (file_name ,filename =file_name )
                await ctx .send (embed =embed ,file =discord_file )

                os .remove (file_name )

            await message .delete ()

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =f"An error occurred: {e }",
            color =discord .Color .red ()
            )
            try :
                await message .edit (embed =error_embed )
            except Exception :
                await ctx .send (embed =error_embed )



async def setup (bot ):
    await bot .add_cog (PendingFeedbackAll (bot ))
