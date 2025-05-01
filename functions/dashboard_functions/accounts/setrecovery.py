

import discord 
from discord .ext import commands 
from discord import ui 
import sqlite3 
import asyncio 
import os 
import random 
import bcrypt 
from functions .recovery_functions .set_recovery_otp_function import send_otp_email ,find_user_database ,is_user_premium 

def fetch_recovery_email (user_id :int )->str :
    """
    Returns 'Set' if a recovery email exists for the user (since it’s stored hashed),
    or returns "No recovery email set yet." otherwise.
    """
    db_directory ="credentialsdatabase"
    db_path =find_user_database (user_id ,db_directory )
    if not db_path :
        return "No recovery email set yet."
    try :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT recovery_email FROM users WHERE user_id = ?",(user_id ,))
        row =cursor .fetchone ()
        conn .close ()
        if row and row [0 ]:
            return "Recovery Email Set."
        else :
            return "No recovery email set yet."
    except Exception :
        return "No recovery email set yet."

async def initiate_recovery_email_setup (interaction :discord .Interaction ):
    """
    Checks premium status and registration, then sends the Recovery Email Setup embed (with the OTP flow)
    to the user via DM.
    """
    if not is_user_premium (interaction .user .id ):
        error_embed =discord .Embed (
        title ="**Upgrade to Lumen Premium**",
        description ="Recovery Email is a premium feature. To access this feature, please consider upgrading to premium.",
        color =0xff0000 ,
        )
        await interaction .response .send_message (embed =error_embed ,ephemeral =True )
        return 

    db_directory ="credentialsdatabase"
    if not os .path .exists (db_directory ):
        os .makedirs (db_directory )
    db_path =find_user_database (interaction .user .id ,db_directory )
    if not db_path :
        error_embed =discord .Embed (
        title ="**Registration Required**",
        description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
        color =0xff0000 ,
        )
        await interaction .response .send_message (embed =error_embed ,ephemeral =True )
        return 

    try :
        conn =sqlite3 .connect (db_path )
        cursor =conn .cursor ()
        cursor .execute ("SELECT user_id FROM users WHERE user_id = ?",(interaction .user .id ,))
        user_exists =cursor .fetchone ()
        conn .close ()

        if not user_exists :
            error_embed =discord .Embed (
            title ="You are not registered with Lumen",
            description ="You are not registered in the system. Please first register yourself using `+register`.",
            color =discord .Color .red (),
            )
            await interaction .response .send_message (embed =error_embed ,ephemeral =True )
            return 


        embed =discord .Embed (
        title ="**Recovery Email Setup**",
        description =(
        "Setting up a recovery email is an important step to ensure your account remains secure.\n\n"
        "**__How to Set Up__**:\n"
        "-# 1. **Click the button below** to begin the setup process.\n"
        "-# 2. Enter a valid recovery email address that you can access.\n"
        "-# 3. Confirm the email address to move forward.\n\n"
        "**__Why a Recovery Email is Important__**:\n"
        "-# - It helps you recover your account in case of password loss.\n"
        "-# - Ensures you receive security alerts and important notifications promptly.\n\n"
        "**__Precautions__**:\n"
        "-# - **Use a trusted and personal email address** for recovery.\n"
        "-# - Ensure that only you have access to the recovery email account.\n"
        "-# - **Do not share your recovery email address** with anyone claiming to be support.\n"
        "-# - Verify all official communications are from our trusted sources.\n\n"
        "**If you encounter any issues, feel free to reach out to our support team for assistance.**"
        ),
        color =0x000001 ,
        )
        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67995814&is=67980694&hm=3b5bc2facb2abd8f9b6f0a7a8438aa7fca328dd8208abc4d8624e23c447f6f5d&=&format=webp&quality=lossless&width=671&height=671")


        view =EnterRecoveryView (interaction .user )
        await interaction .user .send (embed =embed ,view =view )
        confirmation_embed =discord .Embed (
        title ="**Recovery Email Setup Notification**",
        description =(
        f"{interaction .user .mention }, a message has been sent to your **Direct Messages (DMs)** to continue the recovery email setup.\n\n"
        "**__Next Steps:__**\n"
        "-# - Check your DMs and follow the instructions provided.\n"
        "-# - Ensure your DMs are open to receive the message.\n\n"
        "**__Troubleshooting:__**\n"
        "-# - If you do not see the DM, check your spam or filtered messages.\n"
        "-# - For further assistance, contact our support team."
        ),
        color =0x000001 
        )
        await interaction .response .send_message (embed =confirmation_embed ,ephemeral =True )

    except discord .Forbidden :
        error_embed =discord .Embed (
        title ="Direct Messages Disabled",
        description ="I couldn't send you a DM. Please enable DMs and try again.",
        color =discord .Color .red (),
        )
        await interaction .response .send_message (embed =error_embed ,ephemeral =True )

    except Exception as e :
        error_embed =discord .Embed (
        title ="Unexpected Error",
        description =f"An unexpected error occurred: {str (e )}",
        color =discord .Color .red (),
        )
        await interaction .response .send_message (embed =error_embed ,ephemeral =True )

class EnterRecoveryView (ui .View ):
    """View containing the 'SET RECOVERY EMAIL' button."""
    def __init__ (self ,user ):
        super ().__init__ (timeout =120 )
        self .user =user 

    @ui .button (label ="SET RECOVERY EMAIL",style =discord .ButtonStyle .secondary )
    async def enter_email (self ,interaction :discord .Interaction ,button :ui .Button ):
        if interaction .user .id !=self .user .id :
            return await interaction .response .send_message ("You cannot use this button.",ephemeral =True )
        await interaction .response .send_modal (EnterRecoveryModal ())

class EnterRecoveryModal (ui .Modal ,title ="Enter Recovery Email"):
    recovery_email =ui .TextInput (
    label ="Enter your Recovery Email",
    placeholder ="example@gmail.com",
    required =True ,
    style =discord .TextStyle .short ,
    )
    confirm_recovery_email =ui .TextInput (
    label ="Re-enter your Recovery Email",
    placeholder ="example@gmail.com",
    required =True ,
    style =discord .TextStyle .short ,
    )

    async def on_submit (self ,interaction :discord .Interaction ):
        email_value =self .recovery_email .value .strip ().lower ()
        confirm_value =self .confirm_recovery_email .value .strip ().lower ()

        if email_value !=confirm_value :
            return await interaction .response .send_message ("Emails do not match. Try again.",ephemeral =True )

        valid_domains =["@gmail.com","@outlook.com","@icloud.com"]
        if not any (email_value .endswith (domain )for domain in valid_domains ):
            return await interaction .response .send_message (
            "Invalid email. Only Gmail, Outlook, or iCloud emails are allowed.",
            ephemeral =True ,
            )


        otp =''.join (random .choices ("0123456789",k =6 ))

        sending_embed =discord .Embed (
        title ="Sending OTP...",
        description ="Please wait while we send an OTP to your email.",
        color =0x000001 ,
        )
        await interaction .response .send_message (embed =sending_embed ,ephemeral =True )

        try :
            await asyncio .to_thread (send_otp_email ,email_value ,otp )
        except Exception as e :
            error_embed =discord .Embed (
            title ="Error Sending OTP",
            description =f"An error occurred while sending OTP: `{e }`",
            color =0xff0000 ,
            )
            return await interaction .followup .send (embed =error_embed ,ephemeral =True )

        otp_sent_embed =discord .Embed (
        title ="**OTP Sent Successfully**",
        description =(
        "An OTP (One-Time Password) has been sent to your registered email address.\n\n"
        "**__Instructions__**:\n"
        "-# - Click the **ENTER OTP** button below to input your code.\n"
        "-# - Ensure you enter the OTP promptly before it expires.\n\n"
        "**__Precautions__**:\n"
        "-# - **Do not share your OTP** with anyone, even if they claim to be support.\n"
        "-# - Verify that the email was sent from our official email address.\n"
        "-# - If you do not see the email, check your **Spam** or **Junk** folder.\n"
        "-# - For any concerns, contact our support team immediately.\n\n"
        "**Stay vigilant and ensure your account remains secure.**"
        ),
        color =0x000001 
        )

        view =OTPRequestView (otp ,email_value )
        await interaction .edit_original_response (embed =otp_sent_embed ,view =view )

class OTPRequestView (ui .View ):
    """
    View that provides an 'ENTER OTP' button.
    When clicked, it opens a modal for the user to enter the OTP.
    """
    def __init__ (self ,otp ,recovery_email ):
        super ().__init__ (timeout =300 )
        self .generated_otp =otp 
        self .recovery_email =recovery_email 

    @ui .button (label ="ENTER OTP",style =discord .ButtonStyle .secondary )
    async def enter_otp_button (self ,interaction :discord .Interaction ,button :ui .Button ):

        if not interaction .response .is_done ():
            await interaction .response .send_modal (
            OTPModal (self .generated_otp ,self .recovery_email )
            )

class OTPModal (ui .Modal ,title ="Enter OTP"):
    otp_input =ui .TextInput (
    label ="OTP",
    placeholder ="Enter the 6-digit OTP",
    required =True ,
    style =discord .TextStyle .short ,
    )

    def __init__ (self ,otp ,recovery_email ):
        super ().__init__ ()
        self .generated_otp =otp 
        self .recovery_email =recovery_email 

    async def on_submit (self ,interaction :discord .Interaction ):
        entered_otp =self .otp_input .value .strip ()
        if entered_otp !=self .generated_otp :
            error_embed =discord .Embed (
            title ="Invalid OTP",
            description =(
            "The OTP you entered does not match our records.\n\n"
            "Please click **ENTER OTP** again to retry."
            ),
            color =discord .Color .red (),
            )
            await interaction .response .edit_message (embed =error_embed ,view =None )
            return 

        confirm_embed =discord .Embed (
        title ="**Confirm Recovery Email**",
        description =(
        f"**__Recovery Email Entered:__** `{self .recovery_email }`\n\n"
        "**__Next Steps__**:\n"
        "-# - Click **Confirm** to save your recovery email.\n"
        "-# - Click **Decline** if you wish to discard or re-enter the email.\n\n"
        "**__Important:__**\n"
        "-# - Ensure the email is correct and accessible.\n"
        "-# - **Do not share your recovery email** with anyone.\n"
        "-# - Double-check for typos to avoid issues during recovery.\n\n"
        "If you encounter any issues, contact our support team."
        ),
        color =discord .Color .green ()
        )

        view =ConfirmRecoveryView (interaction .user ,self .recovery_email )
        await interaction .response .edit_message (embed =confirm_embed ,view =view )

class ConfirmRecoveryView (ui .View ):
    """Confirmation view with Confirm and Decline buttons for Recovery Email."""
    def __init__ (self ,user ,recovery_email ):
        super ().__init__ (timeout =120 )
        self .user =user 
        self .recovery_email =recovery_email 

    @ui .button (label ="Confirm",style =discord .ButtonStyle .success )
    async def confirm (self ,interaction :discord .Interaction ,button :ui .Button ):
        if interaction .user .id !=self .user .id :
            return await interaction .response .send_message (
            "You cannot use this button.",ephemeral =True 
            )
        await self .save_to_database (interaction )

    @ui .button (label ="Decline",style =discord .ButtonStyle .danger )
    async def cancel (self ,interaction :discord .Interaction ,button :ui .Button ):
        if interaction .user .id !=self .user .id :
            return await interaction .response .send_message (
            "You cannot use this button.",ephemeral =True 
            )
        cancelled_embed =discord .Embed (
        title ="Recovery Email Setup Cancelled",
        description ="Your recovery email was **not saved**.",
        color =discord .Color .red (),
        )
        await interaction .response .edit_message (embed =cancelled_embed ,view =None )

    async def save_to_database (self ,interaction :discord .Interaction ):
        db_directory ="credentialsdatabase"
        db_path =find_user_database (self .user .id ,db_directory )
        if not db_path :
            error_embed =discord .Embed (
            title ="Error",
            description ="Your account could not be found in the database. Please contact support.",
            color =discord .Color .red (),
            )
            await interaction .response .edit_message (embed =error_embed ,view =None )
            return 

        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()


            cursor .execute (
            '''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    recovery_email TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    key TEXT UNIQUE NOT NULL
                )
                '''
            )


            recovery_email_bytes =self .recovery_email .encode ('utf-8')
            hashed_recovery_email =bcrypt .hashpw (recovery_email_bytes ,bcrypt .gensalt ())
            hashed_recovery_email_str =hashed_recovery_email .decode ('utf-8')

            cursor .execute (
            "SELECT 1 FROM users WHERE user_id = ?",
            (self .user .id ,)
            )
            result =cursor .fetchone ()

            if result :
                cursor .execute (
                "UPDATE users SET recovery_email = ? WHERE user_id = ?",
                (hashed_recovery_email_str ,self .user .id ),
                )
            else :
                cursor .execute (
                """INSERT INTO users (
                        user_id, 
                        username,
                        password,
                        recovery_email,
                        created_by,
                        created_at,
                        key
                    )
                    VALUES (?, 'unknown', 'unknown', ?, 'system', 'unknown', 'placeholder')""",
                (self .user .id ,hashed_recovery_email_str ,)
                )

            conn .commit ()
            conn .close ()

            success_embed =discord .Embed (
            title ="Recovery Email Setup Complete",
            description =(
            f"Your recovery email `{self .recovery_email }` has been saved successfully.\n\n"
            "Stay secure! If you have any questions or issues, contact our support."
            ),
            color =discord .Color .green (),
            )

            await interaction .response .edit_message (embed =success_embed ,view =None )

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error Saving Recovery Email",
            description =(
            "An error occurred while saving your email.\n"
            f"```{str (e )}```"
            ),
            color =discord .Color .red (),
            )
            await interaction .response .edit_message (embed =error_embed ,view =None )
