import discord 
from discord import Embed 
from discord .ext import commands 
from discord .ui import View ,Button ,Modal ,TextInput 
import sqlite3 
import bcrypt 
import os 
import io 
import logging 
from datetime import datetime 
from pytz import timezone 
import asyncio 
import tempfile 



import config 


logging .basicConfig (
filename ='bot.log',
level =logging .INFO ,
format ='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)
logger =logging .getLogger (__name__ )


DELETION_DB_DIR ="datadeletionrequests"
os .makedirs (DELETION_DB_DIR ,exist_ok =True )
DELETION_DB_PATH =os .path .join (DELETION_DB_DIR ,"deletion_requests.db")


def init_deletion_db ():
    try :
        conn =sqlite3 .connect (DELETION_DB_PATH )
        cursor =conn .cursor ()
        cursor .execute ("""
        CREATE TABLE IF NOT EXISTS deletion_requests (
            user_id TEXT PRIMARY KEY,
            reason TEXT NOT NULL,
            requested_on TEXT NOT NULL
        )
        """)
        conn .commit ()
        conn .close ()
        logger .info ("Deletion requests database initialized.")
    except Exception as e :
        logger .error (f"Error initializing deletion requests database: {e }")

init_deletion_db ()


def is_user_registered (user_id :int )->bool :
    credentials_dir ="credentialsdatabase"
    try :

        for db_file in os .listdir (credentials_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (credentials_dir ,db_file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()

                cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
                result =cursor .fetchone ()
                conn .close ()
                if result :
                    return True 
        return False 
    except Exception as e :
        logger .error (f"Error checking registration for user {user_id }: {e }")
        return False 


def get_user_email (user_id :int ):
    credentials_dir ="credentialsdatabase"
    try :
        for db_file in os .listdir (credentials_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (credentials_dir ,db_file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT email FROM users WHERE user_id = ?",(user_id ,))
                row =cursor .fetchone ()
                conn .close ()
                if row :
                    return row [0 ]
        return None 
    except Exception as e :
        logger .error (f"Error fetching email for user {user_id }: {e }")
        return None 


def has_pending_request (user_id :str )->bool :
    try :
        conn =sqlite3 .connect (DELETION_DB_PATH )
        cursor =conn .cursor ()
        cursor .execute ("SELECT 1 FROM deletion_requests WHERE user_id = ?",(user_id ,))
        result =cursor .fetchone ()
        conn .close ()
        return result is not None 
    except Exception as e :
        logger .error (f"Error checking pending request for user {user_id }: {e }")
        return False 


class DataDeletionRequestView (View ):
    """View that holds the Request Data Deletion button."""
    def __init__ (self ,bot :commands .Bot ,user :discord .User ):
        super ().__init__ (timeout =None )
        self .bot =bot 
        self .user =user 

        self .add_item (RequestDeletionButton (bot ,user ))

class RequestDeletionButton (Button ):
    """Button to initiate a data deletion request."""
    def __init__ (self ,bot :commands .Bot ,user :discord .User ):
        super ().__init__ (label ="Request Data Deletion",style =discord .ButtonStyle .danger )
        self .bot =bot 
        self .user =user 

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .user :
            await interaction .response .send_message ("You are not authorized to use this button.",ephemeral =True )
            return 

        user_id =str (self .user .id )
        if has_pending_request (user_id ):

            pending_embed =Embed (
            title ="Pending Deletion Request",
            description =(
            "You already have a pending data deletion request.\n\n"
            "For support, kindly contact the Lumen Support Server."
            ),
            color =0xFFA500 
            )
            support_view =SupportTicketView ()
            await interaction .response .edit_message (embed =pending_embed ,view =support_view )
            return 


        await interaction .response .send_modal (RequestDeletionModal (self .bot ,self .user ,original_message =interaction .message ))

class RequestDeletionModal (Modal ):
    """Modal that asks for the detailed reason for deletion and password."""
    def __init__ (self ,bot :commands .Bot ,user :discord .User ,original_message :discord .Message ):
        super ().__init__ (title ="Request Data Deletion")
        self .bot =bot 
        self .user =user 
        self .original_message =original_message 

        self .reason =TextInput (
        label ="Detailed Reason for Deletion",
        style =discord .TextStyle .paragraph ,
        required =True ,
        placeholder ="Please describe why you want your data deleted..."
        )
        self .add_item (self .reason )

        self .password =TextInput (
        label ="Please enter your password",
        style =discord .TextStyle .short ,
        min_length =6 ,
        max_length =100 ,
        required =True ,
        placeholder ="Your account password"
        )
        self .add_item (self .password )

    async def on_submit (self ,interaction :discord .Interaction ):

        await interaction .response .defer (thinking =True )
        user_id =str (self .user .id )
        password_input =self .password .value .strip ()
        reason_input =self .reason .value .strip ()

        try :

            if not is_user_registered (self .user .id ):
                await interaction .followup .send (
                "You must be registered with Lumen to request data deletion.",ephemeral =True 
                )
                return 


            credentials_dir ="credentialsdatabase"
            stored_password_hash =None 
            for db_file in os .listdir (credentials_dir ):
                if db_file .endswith (".db"):
                    db_path =os .path .join (credentials_dir ,db_file )
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT password FROM users WHERE user_id = ?",(user_id ,))
                    row =cursor .fetchone ()
                    conn .close ()
                    if row :
                        stored_password_hash =row [0 ]
                        break 

            if not stored_password_hash :
                await interaction .followup .send ("No credentials found for your account.",ephemeral =True )
                return 

            if not bcrypt .checkpw (password_input .encode ('utf-8'),stored_password_hash .encode ('utf-8')):
                await interaction .followup .send ("Incorrect password. Data deletion request aborted.",ephemeral =True )
                return 


            conn =sqlite3 .connect (DELETION_DB_PATH )
            cursor =conn .cursor ()
            tz =timezone ("Asia/Kolkata")
            requested_on =datetime .now (tz ).strftime ("%Y-%m-%d %H:%M:%S")
            cursor .execute ("""
            INSERT OR REPLACE INTO deletion_requests (user_id, reason, requested_on)
            VALUES (?, ?, ?)
            """,(user_id ,reason_input ,requested_on ))
            conn .commit ()
            conn .close ()
            logger .info (f"User {user_id }: Data deletion request recorded at {requested_on }.")


            review_embed =Embed (
            title ="Data Deletion Request",
            description =(
            f"**Username:** {self .user .name }\n"
            f"**User Mention:** {self .user .mention }\n"
            f"**Display Name:** {self .user .display_name }\n"
            f"**User ID:** {user_id }\n"
            f"**Reason:** {reason_input }\n"
            f"**Requested On:** {requested_on } (Asia/Kolkata)"
            ),
            color =0xFF4500 
            )
            review_view =ReviewActionView (self .bot ,self .user )
            review_msg =None 
            try :
                channel =self .bot .get_channel (config .DELETION_REQUEST_CHANNEL_ID )
                if channel :
                    review_msg =await channel .send (embed =review_embed ,view =review_view )
                    logger .info (f"User {user_id }: Deletion request sent to review channel.")
                else :
                    logger .error ("Deletion request channel not found. Check DELETION_REQUEST_CHANNEL_ID in config.py.")
            except Exception as e :
                logger .error (f"Error sending deletion request to review channel: {e }")


            updated_embed =Embed (
            title ="Deletion Requested",
            description =(
            "Your data deletion request has been recorded.\n\n"
            "Your data will be processed after a 7-day review period. "
            "If you wish to cancel your request within these 7 days, please click the **Cancel Deletion** button below."
            ),
            color =0xFFA500 
            )
            cancellation_view =CancellationView (self .bot ,self .user ,requested_on ,review_message =review_msg )


            await self .original_message .edit (embed =updated_embed ,view =cancellation_view )


            message =await interaction .followup .send (
            content ="Your data deletion request has been successfully submitted.",
            ephemeral =False 
            )


            await asyncio .sleep (1 )
            await message .delete ()

        except Exception as e :

            logger .error (f"Error processing data deletion request for user {user_id }: {e }")
            await interaction .followup .send (
            "An error occurred while processing your request. Please try again later.",ephemeral =True 
            )


class CancellationView (View ):
    """
    View containing the Cancel Deletion button.
    The button remains active for 7 days from the request timestamp.
    """
    def __init__ (self ,bot :commands .Bot ,user :discord .User ,requested_on :str ,review_message :discord .Message ):
        super ().__init__ (timeout =None )
        self .bot =bot 
        self .user =user 
        self .requested_on =requested_on 
        self .review_message =review_message 
        self .add_item (CancelDeletionButton (bot ,user ,requested_on ,review_message ))

class CancelDeletionButton (Button ):
    def __init__ (self ,bot :commands .Bot ,user :discord .User ,requested_on :str ,review_message :discord .Message ):
        super ().__init__ (label ="Cancel Deletion",style =discord .ButtonStyle .secondary )
        self .bot =bot 
        self .user =user 
        self .requested_on =requested_on 
        self .review_message =review_message 

    async def callback (self ,interaction :discord .Interaction ):
        user_id =str (self .user .id )


        try :
            conn =sqlite3 .connect (DELETION_DB_PATH )
            cursor =conn .cursor ()
            cursor .execute ("DELETE FROM deletion_requests WHERE user_id = ?",(user_id ,))
            conn .commit ()
            conn .close ()
            logger .info (f"User {user_id }: Data deletion request cancelled and removed from database.")
        except Exception as e :
            logger .error (f"Error deleting data deletion request for user {user_id }: {e }")
            await interaction .response .send_message ("An error occurred while canceling your request. Please try again later.",ephemeral =True )
            return 


        cancel_embed =Embed (
        title ="Request Cancelled",
        description =f"Your data deletion request has been successfully cancelled.",
        color =0xFF0000 
        )


        await interaction .message .edit (embed =cancel_embed ,view =None )


        if self .review_message is not None :
            try :
                await self .review_message .edit (embed =cancel_embed ,view =None )
            except Exception as e :
                logger .error (f"Error editing review message: {e }")

        logger .info (f"User {user_id }: Data deletion request cancelled.")

class ReviewActionView (View ):
    """
    View containing the VERIFY DELETION button for moderators.
    """
    def __init__ (self ,bot :commands .Bot ,requester :discord .User ):
        super ().__init__ (timeout =None )
        self .bot =bot 
        self .requester =requester 
        self .add_item (VerifyDeletionButton (bot ,requester ))

class VerifyDeletionButton (Button ):
    def __init__ (self ,bot :commands .Bot ,requester :discord .User ):
        super ().__init__ (label ="VERIFY DELETION",style =discord .ButtonStyle .success )
        self .bot =bot 
        self .requester =requester 

    async def callback (self ,interaction :discord .Interaction ):

        embed =Embed (
        title ="Data Deletion Verification",
        description =(
        "Your data deletion request is ready for verification. "
        "Please create a support ticket at the Lumen Support Server for data deletion verification."
        ),
        color =0x0000FF 
        )
        support_view =SupportTicketView ()
        try :
            await self .requester .send (embed =embed ,view =support_view )
            await interaction .response .send_message ("A verification instruction has been sent to the requester.",ephemeral =True )
            logger .info (f"Verification instruction sent to user {self .requester .id }.")
        except discord .Forbidden :
            await interaction .response .send_message ("Could not send a DM to the requester. They may have DMs disabled.",ephemeral =True )
            logger .warning (f"Failed to send DM to user {self .requester .id } for deletion verification.")

class SupportTicketView (View ):
    """
    View containing a link button to the Lumen Support Server.
    """
    def __init__ (self ):
        super ().__init__ (timeout =None )
        self .add_item (DiscordSupportButton ())

class DiscordSupportButton (Button ):
    def __init__ (self ):
        super ().__init__ (label ="Lumen Support Server",style =discord .ButtonStyle .link ,url ="https://discord.gg/lumenreport")


class DataDeletionRequest (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ='requestdatadeletion')
    async def request_deletion_command (self ,ctx :commands .Context ):
        """
        Sends a DM to the user with an option to request deletion of their personal data.
        """
        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="Registration Required",
            description ="You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 

        dm_embed =Embed (
        title ="Data Deletion Request",
        description =(
        "You have the right to request the deletion of your personal data from Lumen databases. "
        "If you choose to proceed, your request will be reviewed for 7 days before processing. "
        "Please click the button below to begin your data deletion request."
        ),
        color =0x000001 
        )
        try :
            view =DataDeletionRequestView (self .bot ,ctx .author )
            await ctx .author .send (embed =dm_embed ,view =view )
            reply_embed =Embed (
            title ="DM Sent",
            description ="I've sent you a Direct Message with instructions for requesting data deletion.",
            color =0x000001 
            )
            await ctx .reply (embed =reply_embed ,ephemeral =True )
        except discord .Forbidden :
            error_embed =Embed (
            title ="DM Failed",
            description =(
            "I couldn't send you a Direct Message. Please check your privacy settings and ensure that "
            "you allow DMs from server members."
            ),
            color =discord .Color .red ()
            )
            await ctx .reply (embed =error_embed ,ephemeral =True )

async def setup (bot :commands .Bot ):
    await bot .add_cog (DataDeletionRequest (bot ))
    logger .info ("DataDeletionRequest Cog has been loaded successfully.")