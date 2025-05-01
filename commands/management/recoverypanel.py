import os 
import sqlite3 
import random 
import discord 
from discord .ext import commands 
from discord .ui import Modal ,TextInput ,View ,Button 
import logging 
from datetime import datetime 
from pytz import timezone 
from config import (
RECOVERY_CHANNEL_ID ,
RECOVERY_APPROVE_CHANNEL_ID ,
RECOVERY_DECLINE_CHANNEL_ID ,
RECOVERY_STAFF_PING ,
MANAGEMENT_ROLE_ID 
)


DATABASE_DIR ="recoverydatabase"
MAX_ENTRIES_PER_DB =10000 

def ensure_database_directory ():
    if not os .path .exists (DATABASE_DIR ):
        os .makedirs (DATABASE_DIR )

def get_db_filepath (db_number :int )->str :
    return os .path .join (DATABASE_DIR ,f"recoveryrequest_{db_number }.db")

def create_table_if_not_exists (db_path :str ):
    conn =sqlite3 .connect (db_path )
    cursor =conn .cursor ()
    cursor .execute ('''CREATE TABLE IF NOT EXISTS pending_recovery (
        recovery_id TEXT PRIMARY KEY,
        previous_user_id TEXT,
        new_user_id TEXT,
        username TEXT,
        password TEXT
    )''')
    conn .commit ()
    conn .close ()

def get_current_database ()->str :
    """
    Returns the filepath for the current database (creating a new one if the last one is full).
    """
    ensure_database_directory ()
    db_number =1 
    while True :
        db_path =get_db_filepath (db_number )
        if not os .path .exists (db_path ):

            create_table_if_not_exists (db_path )
            return db_path 
        else :

            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT COUNT(*) FROM pending_recovery")
            count =cursor .fetchone ()[0 ]
            conn .close ()
            if count <MAX_ENTRIES_PER_DB :
                return db_path 
            else :
                db_number +=1 

def check_duplicate_request (previous_user_id :str ,new_user_id :str )->bool :
    """
    Check across all recovery databases if either the previous_user_id or new_user_id
    already has a pending request.
    Returns True if a duplicate is found.
    """
    ensure_database_directory ()

    for filename in os .listdir (DATABASE_DIR ):
        if filename .startswith ("recoveryrequest_")and filename .endswith (".db"):
            db_path =os .path .join (DATABASE_DIR ,filename )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT recovery_id FROM pending_recovery WHERE previous_user_id = ? OR new_user_id = ?",
            (previous_user_id ,new_user_id ))
            result =cursor .fetchone ()
            conn .close ()
            if result is not None :
                return True 
    return False 

async def delete_recovery_id_from_db (recovery_id :str ):
    """
    Delete the recovery entry from whichever database it is in.
    """
    ensure_database_directory ()
    for filename in os .listdir (DATABASE_DIR ):
        if filename .startswith ("recoveryrequest_")and filename .endswith (".db"):
            db_path =os .path .join (DATABASE_DIR ,filename )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("DELETE FROM pending_recovery WHERE recovery_id = ?",(recovery_id ,))
            conn .commit ()
            conn .close ()


def generate_recovery_id ()->str :
    """Generate a unique 16-digit recovery ID."""
    return ''.join ([str (random .randint (0 ,9 ))for _ in range (16 )])


class RecoveryForm (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    class RecoveryModal (Modal ):
        def __init__ (self ,user_id ):
            super ().__init__ (title ="Recovery Form")
            self .new_user_id =str (user_id )

            self .username =TextInput (label ="Username",placeholder ="Enter your username")
            self .password =TextInput (label ="Password",placeholder ="Enter your password")
            self .previous_user_id =TextInput (label ="Previous User ID",placeholder ="Enter your previous user ID")
            self .add_item (self .username )
            self .add_item (self .password )
            self .add_item (self .previous_user_id )

        async def on_submit (self ,interaction :discord .Interaction ):

            if check_duplicate_request (self .previous_user_id .value ,self .new_user_id ):
                await interaction .response .send_message ("You already have a pending recovery request.",ephemeral =True )
                return 

            recovery_id =generate_recovery_id ()
            db_path =get_current_database ()
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ('''INSERT INTO pending_recovery (recovery_id, previous_user_id, new_user_id, username, password)
                VALUES (?, ?, ?, ?, ?)''',
                (recovery_id ,self .previous_user_id .value ,self .new_user_id ,self .username .value ,self .password .value ))
                conn .commit ()
                conn .close ()


                await interaction .response .send_message (f"Your recovery request has been submitted! Recovery ID: `{recovery_id }`",ephemeral =True )


                log_embed =discord .Embed (title ="New Recovery Request",color =0xffb03b )
                log_embed .add_field (name ="Recovery ID",value =f"```\n{recovery_id }\n```",inline =False )
                log_embed .add_field (name ="Username",value =f"```\n{self .username .value }\n```",inline =False )
                log_embed .add_field (name ="Previous User ID",value =f"```\n{self .previous_user_id .value }\n```",inline =True )
                log_embed .add_field (name ="New User ID",value =f"```\n{self .new_user_id }\n```",inline =True )


                recovery_staff_mention =f"<@&{RECOVERY_STAFF_PING }>"
                recovery_channel =interaction .client .get_channel (RECOVERY_CHANNEL_ID )
                if recovery_channel :
                    await recovery_channel .send (content =recovery_staff_mention ,embed =log_embed )
                else :
                    logging .error ("Recovery channel not found.")

                logging .info (f"Recovery request submitted: {recovery_id }")


                try :
                    previous_user =await interaction .client .fetch_user (int (self .previous_user_id .value ))
                except Exception as e :
                    logging .error (f"Error fetching previous user: {e }")
                    return 

                embed =discord .Embed (
                title ="Profile Recovery Request Received",
                description =(
                f"Hello {previous_user .mention },\n\n"
                "A Lumen Profile Recovery Request has been made claiming to be you. Please respond to this message ASAP to Accept/Decline this request.\n"
                "You have 24 hours from this message to respond.\n\n"
                "Failure to respond may result in a loss of your profile & unintended consequences."
                ),
                color =0xffb03b 
                )
                embed .add_field (name ="Recovery ID",value =f"```{recovery_id }```",inline =False )
                embed .add_field (name ="Username",value =f"```{self .username .value }```",inline =False )
                embed .add_field (name ="New User ID",value =f"```{self .new_user_id }```",inline =False )
                embed .timestamp =discord .utils .utcnow ()

                view =RecoveryResponseView (recovery_id )
                await previous_user .send (embed =embed ,view =view )

            except Exception as e :
                logging .error (f"Error submitting recovery request: {e }")
                await interaction .response .send_message ("An error occurred while processing your request. Please try again later.",ephemeral =True )



class RecoveryResponseView (View ):
    def __init__ (self ,recovery_id ):
        super ().__init__ (timeout =86400 )
        self .recovery_id =recovery_id 

    async def disable_buttons (self ,interaction =None ):
        for item in self .children :
            if isinstance (item ,Button ):
                item .disabled =True 
        if interaction :
            await interaction .message .edit (view =self )

    async def on_timeout (self ):
        logging .info (f"View timeout triggered for Recovery ID: {self .recovery_id }")
        await self .disable_buttons ()

    @discord .ui .button (label ="ACCEPT RECOVERY",style =discord .ButtonStyle .success )
    async def accept_callback (self ,interaction :discord .Interaction ,button :Button ):

        kolkata_time =discord .utils .utcnow ().astimezone (timezone ('Asia/Kolkata'))
        embed =discord .Embed (
        title ="Recovery Request Approved",
        description =f"The following Recovery ID has been approved ```{self .recovery_id }```",
        color =0xffb03b 
        )
        embed .timestamp =discord .utils .utcnow ()
        embed .add_field (name ="Action Taken By",value =f"`{interaction .user }`",inline =False )
        embed .add_field (name ="Timestamp",value =f"{kolkata_time .strftime ('%Y-%m-%d %H:%M:%S')} IST",inline =False )


        recovery_staff_mention =f"<@&{RECOVERY_STAFF_PING }>"
        approve_channel =interaction .client .get_channel (RECOVERY_APPROVE_CHANNEL_ID )
        if approve_channel :
            await approve_channel .send (content =recovery_staff_mention ,embed =embed )
        else :
            logging .error ("Approval channel not found.")

        await interaction .response .send_message ("You have accepted the recovery request.",ephemeral =True )
        await self .disable_buttons (interaction )

    @discord .ui .button (label ="DECLINE RECOVERY",style =discord .ButtonStyle .danger )
    async def decline_callback (self ,interaction :discord .Interaction ,button :Button ):

        kolkata_time =discord .utils .utcnow ().astimezone (timezone ('Asia/Kolkata'))
        embed =discord .Embed (
        title ="Recovery Request Declined",
        description =f"The following Recovery ID has been declined ```{self .recovery_id }```",
        color =discord .Color .red ()
        )
        embed .timestamp =discord .utils .utcnow ()
        embed .add_field (name ="Action Taken By",value =f"`{interaction .user }`",inline =False )
        embed .add_field (name ="Timestamp",value =f"{kolkata_time .strftime ('%Y-%m-%d %H:%M:%S')} IST",inline =False )

        recovery_staff_mention =f"<@&{RECOVERY_STAFF_PING }>"
        reject_channel =interaction .client .get_channel (RECOVERY_DECLINE_CHANNEL_ID )
        if reject_channel :
            await reject_channel .send (content =recovery_staff_mention ,embed =embed )
        else :
            logging .error ("Rejection channel not found.")


        await delete_recovery_id_from_db (self .recovery_id )
        await interaction .response .send_message ("You have declined the recovery request.",ephemeral =True )
        await self .disable_buttons (interaction )



class RecoveryView (View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )

    @discord .ui .button (label ="RECOVER PROFILE",style =discord .ButtonStyle .success ,custom_id ="recover_button_unique")
    async def recover_button_callback (self ,interaction :discord .Interaction ,button :Button ):
        user_id =interaction .user .id 
        await interaction .response .send_modal (RecoveryForm .RecoveryModal (user_id ))




class RecoveryPanel (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def recoverypanel (self ,ctx ):

        if not any (role .id ==MANAGEMENT_ROLE_ID for role in ctx .author .roles ):
            await ctx .send ("You don't have permission to use this command.")
            return 

        embed =discord .Embed (
        title ="**Account Recovery Panel**",
        description =(
        "Switching your accounts? Use this panel to submit an account Lumen Profile recovery request.\n\n"
        "**__How It Works__**:\n"
        "-# 1. Click the button below to start the recovery process.\n"
        "-# 2. You will be asked to provide the following details:\n"
        "-#    - Your **previous User ID**.\n"
        "-#    - Your **registered Username**.\n"
        "-#    - Your **previous Password**.\n"
        "-# 3. Once submitted, your request will be processed by our admin team.\n"
        "-# 4. A **Recovery ID** will be sent to your registered email for further steps.\n\n"
        "**__Important Information__**:\n"
        "-# 1. Ensure all details provided are accurate to avoid delays.\n"
        "-# 2. The review process may take some time, so please be patient.\n\n"
        "**__Precautions__**:\n"
        "-# 1. **Do not share your Recovery ID** or account details with anyone.\n"
        "-# 2. Verify that the request was initiated by you.\n"
        "-# 3. If you suspect unauthorized activity, contact our support team immediately.\n"
        "-# 4. Always double-check you are on our official platform before proceeding.\n\n"
        "**For additional help, reach out to our Support Team at <#1324112287480545411>.**"
        ),
        color =0x000001 
        )
        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
        view =RecoveryView ()
        await ctx .send (embed =embed ,view =view )



async def setup (bot ):
    await bot .add_cog (RecoveryPanel (bot ))