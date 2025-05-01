import discord 
from discord .ext import commands 
import sqlite3 
from config import MANAGEMENT_ROLE_ID 
import os 
from datetime import datetime 


VERIFICATION_DATABASE_DIR ="verificationdatabase"
PREMIUM_VERIFICATION_DATABASE_DIR ="premiumverificationfeedback"

def create_db_connection (db_path ):
    """Helper function to create and return a database connection."""
    conn =sqlite3 .connect (db_path )
    return conn 

class PendingVerificationFball (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="pendingverificationfball")
    async def pendingverificationfball (self ,ctx ,category :str =None ):
        """
        Fetches all pending verification feedbacks from one or both directories and sends them as .txt file(s).
        
        Usage:
          +pendingverificationfball                -> Fetch from both directories.
          +pendingverificationfball premium        -> Fetch only from premiumverificationfeedback.
          +pendingverificationfball normal         -> Fetch only from verificationdatabase.
          
        This command can only be used by users with the MANAGEMENT_ROLE_ID.
        """
        try :

            if not any (role .id in MANAGEMENT_ROLE_ID for role in ctx .author .roles ):
                embed =discord .Embed (
                title ="**Permission Denied**",
                description ="You do not have the required permissions to use this command.",
                color =0x000001 
                )
                await ctx .send (embed =embed )
                return 



            directories =[]
            if category is None :

                directories =[
                (VERIFICATION_DATABASE_DIR ,"No"),
                (PREMIUM_VERIFICATION_DATABASE_DIR ,"Yes")
                ]
            else :
                category_lower =category .lower ()
                if category_lower =="premium":
                    directories =[(PREMIUM_VERIFICATION_DATABASE_DIR ,"Yes")]
                elif category_lower =="normal":
                    directories =[(VERIFICATION_DATABASE_DIR ,"No")]
                else :
                    embed =discord .Embed (
                    title ="**Invalid Category**",
                    description ="The category must be either `premium` or `normal`, or omitted to fetch from both.",
                    color =0x000001 
                    )
                    await ctx .send (embed =embed )
                    return 


            feedback_entries =[]


            header_lines =[]
            header_lines .append ("PENDING FEEDBACK LIST")
            header_lines .append (f"REQUESTED BY: {ctx .author }")

            current_timestamp =datetime .now ().strftime ("%d/%m/%Y %I:%M %p IST")
            header_lines .append (f"TIMESTAMP: {current_timestamp }")
            header_lines .append ("")

            header_text ="\n".join (header_lines )


            for db_dir ,premium_flag in directories :

                if not os .path .exists (db_dir ):
                    continue 

                for file in os .listdir (db_dir ):
                    if file .endswith (".db"):
                        db_path =os .path .join (db_dir ,file )

                        try :
                            conn =create_db_connection (db_path )
                            cursor =conn .cursor ()
                            cursor .execute ("SELECT * FROM pending_feedback")
                            feedbacks =cursor .fetchall ()
                        except Exception as db_err :
                            print (f"Error reading {db_path }: {db_err }")
                            continue 
                        finally :
                            conn .close ()


                        for feedback in feedbacks :


                            try :
                                vouch_number ,giver_id ,receiver_id ,feedback_text ,timestamp ,feedback_type =feedback 
                            except Exception as unpack_err :
                                print (f"Error unpacking feedback from {db_path }: {unpack_err }")
                                continue 


                            if len (feedback_text )>1000 :
                                feedback_text =feedback_text [:997 ]+"..."

                            entry =(
                            f"Feedback ID: {vouch_number }\n"
                            f"Receiver ID: {receiver_id }\n"
                            f"Giver ID: {giver_id }\n"
                            f"Feedback: {feedback_text }\n"
                            f"Feedback Type: {feedback_type }\n"
                            f"Verification Requested On: {timestamp }\n"
                            f"Premium: {premium_flag }\n"
                            "--------------------------------------------------\n"
                            )
                            feedback_entries .append (entry )



            if not feedback_entries :
                embed =discord .Embed (
                title ="**No Pending Feedbacks Found**",
                description ="There are no pending verification feedbacks in the selected directory(ies).",
                color =0x000001 
                )
                await ctx .send (embed =embed )
                return 







            MAX_ENTRIES_PER_FILE =5000 


            feedback_chunks =[
            feedback_entries [i :i +MAX_ENTRIES_PER_FILE ]
            for i in range (0 ,len (feedback_entries ),MAX_ENTRIES_PER_FILE )
            ]


            for index ,chunk in enumerate (feedback_chunks ,start =1 ):

                file_content =header_text +"\n"+"".join (chunk )


                from io import BytesIO 
                file_buffer =BytesIO (file_content .encode ("utf-8"))
                file_buffer .seek (0 )


                file_name =f"pending_verification_feedbacks_{index }.txt"
                discord_file =discord .File (fp =file_buffer ,filename =file_name )


                embed =discord .Embed (
                title ="Pending Verification Feedbacks",
                description =f"Attached is file **{file_name }** containing the pending feedbacks.",
                color =0x000001 
                )

                await ctx .send (embed =embed ,file =discord_file )



        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =f"An unexpected error occurred: {e }",
            color =0x000001 
            )
            await ctx .send (embed =error_embed )

    @pendingverificationfball .error 
    async def pendingverificationfball_error (self ,ctx ,error ):
        """
        Error handler for the pendingverificationfball command.
        Provides user-friendly messages for missing or invalid arguments.
        """
        if isinstance (error ,commands .MissingRequiredArgument ):
            embed =discord .Embed (
            title ="**Missing Argument**",
            description ="Usage:\n`+pendingverificationfball`\n`+pendingverificationfball premium`\n`+pendingverificationfball normal`",
            color =0x000001 
            )
            await ctx .send (embed =embed )
        elif isinstance (error ,commands .BadArgument ):
            embed =discord .Embed (
            title ="**Invalid Argument**",
            description ="The argument provided is invalid. Use either `premium`, `normal`, or omit the argument to fetch from both directories.",
            color =0x000001 
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="Error",
            description =f"An unexpected error occurred: {error }",
            color =0x000001 
            )
            await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (PendingVerificationFball (bot ))
