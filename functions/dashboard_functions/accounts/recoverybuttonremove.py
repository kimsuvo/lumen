

import discord 
import sqlite3 
import os 
from functions .recovery_functions .set_recovery_otp_function import find_user_database 

def remove_recovery_email_from_db (user_id :int )->bool :
    """
    Removes the recovery email from the user's record (by setting it to an empty string).
    Returns True if successful, False otherwise.
    """
    db_directory ="credentialsdatabase"
    db_path =find_user_database (user_id ,db_directory )
    if not db_path :
        return False 
    try :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("UPDATE users SET recovery_email = '' WHERE user_id = ?",(user_id ,))
        conn .commit ()
        conn .close ()
        return True 
    except Exception as e :
        print ("Error removing recovery email:",e )
        return False 

class ConfirmRemoveRecoveryEmailView (discord .ui .View ):
    """Confirmation view with Confirm and Cancel buttons for removing the recovery email."""
    def __init__ (self ,user :discord .User ):
        super ().__init__ (timeout =120 )
        self .user =user 

    @discord .ui .button (label ="Confirm",style =discord .ButtonStyle .success )
    async def confirm (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

        if interaction .user .id !=self .user .id :
            return await interaction .response .send_message ("You cannot use this button.",ephemeral =True )
        success =remove_recovery_email_from_db (self .user .id )
        if success :
            embed =discord .Embed (
            title ="Recovery Email Removed",
            description ="Your recovery email has been successfully removed.",
            color =discord .Color .green (),
            )
        else :
            embed =discord .Embed (
            title ="Error",
            description ="An error occurred while removing your recovery email. Please try again later.",
            color =discord .Color .red (),
            )
        await interaction .response .edit_message (embed =embed ,view =None )

    @discord .ui .button (label ="Cancel",style =discord .ButtonStyle .danger )
    async def cancel (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user .id !=self .user .id :
            return await interaction .response .send_message ("You cannot use this button.",ephemeral =True )
        embed =discord .Embed (
        title ="Recovery Email Removal Cancelled",
        description ="Your recovery email was not removed.",
        color =discord .Color .blue (),
        )
        await interaction .response .edit_message (embed =embed ,view =None )

async def initiate_remove_recovery_email (interaction :discord .Interaction ):
    """
    Initiates the removal process by sending an ephemeral confirmation embed
    with Confirm and Cancel buttons.
    """
    embed =discord .Embed (
    title ="Confirm Recovery Email Removal",
    description ="Are you sure you want to remove your recovery email?",
    color =0x000001 ,
    )
    view =ConfirmRemoveRecoveryEmailView (interaction .user )
    await interaction .response .send_message (embed =embed ,view =view ,ephemeral =True )
