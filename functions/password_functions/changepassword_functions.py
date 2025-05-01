

import os 
import sqlite3 
import bcrypt 
import pytz 
from typing import Tuple 
from datetime import datetime 
import discord 
from discord import Embed 
from discord .ui import Button ,View 


CREDENTIALS_DATABASE_DIR ="credentialsdatabase"


def is_user_registered (user_id )->bool :
    """Check if a user is registered in any of the database files."""
    for db_file in os .listdir (CREDENTIALS_DATABASE_DIR ):
        if db_file .endswith (".db"):
            db_path =os .path .join (CREDENTIALS_DATABASE_DIR ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
    return False 


def is_strong_password (password :str )->Tuple [bool ,str ]:
    """Return whether a password is strong (currently, that it contains no spaces)."""
    if " "in password :
        return False ,"Password must not contain any spaces."
    return True ,""


def update_user_password (user_id :str ,provided_username :str ,previous_password :str ,new_password :str )->Tuple [bool ,str ]:
    """
    Attempt to update the user’s password.
    
    Checks include:
      - User exists in one of the databases
      - The provided username matches (using bcrypt check)
      - The previous password is correct
      - The new password meets strength requirements and is not the same as the old one

    Returns a tuple: (success: bool, message: str)
    """
    db_dir =CREDENTIALS_DATABASE_DIR 
    if not os .path .isdir (db_dir ):
        return False ,"Database directory not found."

    db_files =[f for f in os .listdir (db_dir )if f .endswith ('.db')]
    user =None 
    stored_username =None 
    stored_password_hash =None 
    conn =None 
    cursor =None 
    try :
        for db_file in db_files :
            db_path =os .path .join (db_dir ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM users WHERE user_id = ?",(user_id ,))
            user =cursor .fetchone ()
            if user :


                stored_username ,stored_password_hash =user [1 ],user [2 ]
                break 
            else :
                conn .close ()
                conn =None 

        if not user :
            return False ,"User not found in the database."

        if not bcrypt .checkpw (provided_username .encode (),stored_username .encode ()):
            return False ,"Username is incorrect."

        if not bcrypt .checkpw (previous_password .encode (),stored_password_hash .encode ()):
            return False ,"Previous password is incorrect."

        valid ,message =is_strong_password (new_password )
        if not valid :
            return False ,f"Invalid password: {message }"

        if bcrypt .checkpw (new_password .encode (),stored_password_hash .encode ()):
            return False ,"New password cannot be the same as the old password."

        new_password_hash =bcrypt .hashpw (new_password .encode (),bcrypt .gensalt ()).decode ()
        cursor .execute ("UPDATE users SET password = ? WHERE user_id = ?",(new_password_hash ,user_id ))
        conn .commit ()
        return True ,"Password updated successfully."

    except Exception as e :
        return False ,f"An error occurred: {e }"

    finally :
        if conn :
            conn .close ()


class PasswordUpdateConfirmationView (View ):
    """A simple View with a button linking to the support server."""
    def __init__ (self ):
        super ().__init__ (timeout =None )
        support_button =Button (label ="Lumen Support Server",url ="https://discord.gg/lumenbot")
        self .add_item (support_button )


class ChangePasswordForm (discord .ui .Modal ,title ="Change Password"):
    """A Modal for entering the account username, current password, and new password."""
    username =discord .ui .TextInput (
    label ="Username",
    placeholder ="Enter your account username",
    required =True 
    )
    previous_password =discord .ui .TextInput (
    label ="Previous Password",
    placeholder ="Enter your current password",
    required =True ,
    style =discord .TextStyle .short 
    )
    new_password =discord .ui .TextInput (
    label ="New Password",
    placeholder ="Enter your new password",
    required =True ,
    style =discord .TextStyle .short 
    )

    async def on_submit (self ,interaction :discord .Interaction ):
        user_id =str (interaction .user .id )
        success ,message =update_user_password (
        user_id =user_id ,
        provided_username =self .username .value ,
        previous_password =self .previous_password .value ,
        new_password =self .new_password .value 
        )
        if not success :
            await interaction .response .send_message (message ,ephemeral =True )
            return 


        embed =Embed (
        title ="**Password Update Confirmation**",
        description =(
        "Your password has been successfully updated. **Keep it secure.**\n\n"
        "**__Precautions__**:\n"
        "-# 1. **Do not share your password** with anyone.\n"
        "-# 2. Ensure your password is **unique** and not used elsewhere.\n"
        "-# 3. Use a combination of **letters, numbers, and special characters** for better security.\n"
        "-# 4. **Avoid clicking on suspicious links** or providing your credentials on untrusted websites.\n\n"
        "If you didn’t request a password change, **report immediately** to [Lumen Support Server](https://discord.gg/lumenbot)."
        ),
        color =0x000001 
        )
        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
        embed .add_field (name ="Account Username",value =f"`{self .username .value }`",inline =False )
        embed .timestamp =datetime .now (pytz .timezone ('Asia/Kolkata'))

        view =PasswordUpdateConfirmationView ()
        try :
            await interaction .user .send (embed =embed ,view =view )
            await interaction .response .send_message ("Password updated successfully! Check your DMs.",ephemeral =True )
        except discord .Forbidden :
            await interaction .response .send_message ("Password updated, but I couldn't send you a DM. Please check your settings.",ephemeral =True )


class ChangePasswordView (View ):
    """A View with a button to launch the ChangePasswordForm modal."""
    def __init__ (self ,bot ):
        super ().__init__ (timeout =60 )
        self .bot =bot 
        support_button =Button (label ="Lumen Support Server",url ="https://discord.gg/lumenbot")
        self .add_item (support_button )

    @discord .ui .button (label ="Change Profile Password",style =discord .ButtonStyle .blurple )
    async def change_password_button (self ,interaction :discord .Interaction ,button :Button ):
        modal =ChangePasswordForm ()
        await interaction .response .send_modal (modal )
