

import discord 
from discord .ext import commands 
from discord .ui import Button ,View 
import os 
import random 
import sqlite3 
import bcrypt 
import smtplib 
from email .mime .text import MIMEText 
from email .mime .multipart import MIMEMultipart 


from functions .password_functions .forgotpassword_functions import verify_email ,send_otp_to_email ,update_password 




class SupportServerButton (View ):
    def __init__ (self ):
        super ().__init__ ()
        support_button =Button (label ="Lumen Support Server",url ="https://discord.gg/lumenreport")
        self .add_item (support_button )




class EmailModal (discord .ui .Modal ,title ="Enter Recovery Email"):
    email_input =discord .ui .TextInput (
    label ="Your Recovery Email",
    placeholder ="Enter your recovery email...",
    style =discord .TextStyle .short ,
    required =True 
    )

    def __init__ (self ,parent_cog ,ctx ):
        super ().__init__ ()
        self .parent_cog =parent_cog 
        self .ctx =ctx 

    async def on_submit (self ,interaction :discord .Interaction ):
        await interaction .response .defer ()
        email =self .email_input .value .strip ()


        if not verify_email (email ,db_dir =self .parent_cog .db_dir ):
            error_embed =discord .Embed (
            title ="Email Not Found",
            description =(
            f"Your recovery email: **{email }** is not in our system.\n"
            "Please check your spelling or try another email."
            ),
            color =discord .Color .red ()
            )
            return await interaction .followup .send (embed =error_embed ,ephemeral =True )


        self .parent_cog .pending_otp [interaction .user .id ]={"email":email ,"otp":None }
        await self .parent_cog .edit_embed_sending_otp (interaction ,email )


        otp =send_otp_to_email (email ,email_accounts =self .parent_cog .email_accounts )
        self .parent_cog .pending_otp [interaction .user .id ]["otp"]=otp 

        await self .parent_cog .edit_embed_step_2 (interaction ,email )




class OTPModal (discord .ui .Modal ,title ="Enter Your OTP"):
    otp_input =discord .ui .TextInput (
    label ="One-Time Passcode",
    placeholder ="Enter your 6-digit OTP",
    style =discord .TextStyle .short ,
    required =True ,
    max_length =6 ,
    min_length =6 
    )

    def __init__ (self ,parent_cog :'PreResetPasswordCog',ctx ):
        super ().__init__ ()
        self .parent_cog =parent_cog 
        self .ctx =ctx 

    async def on_submit (self ,interaction :discord .Interaction ):
        user_id =interaction .user .id 
        user_data =self .parent_cog .pending_otp .get (user_id )
        if not user_data :
            error_embed =discord .Embed (
            title ="**No OTP Pending**",
            description ="You have no OTP pending verification. Please restart the process.",
            color =discord .Color .red ()
            )
            return await interaction .response .send_message (embed =error_embed ,ephemeral =True )

        entered_otp =self .otp_input .value .strip ()
        correct_otp =user_data ["otp"]

        if entered_otp ==correct_otp :

            await self .parent_cog .edit_embed_step_3 (interaction )
        else :
            error_embed =discord .Embed (
            title ="**Incorrect OTP**",
            description ="The OTP you entered is invalid. Please try again or restart.",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =error_embed ,ephemeral =True )




class NewPasswordModal (discord .ui .Modal ,title ="Set Your New Password"):
    """Modal for setting a new password."""
    new_password =discord .ui .TextInput (
    label ="New Password",
    placeholder ="Enter your new password",
    style =discord .TextStyle .short ,
    required =True ,
    min_length =8 
    )

    def __init__ (self ,parent_cog :'PreResetPasswordCog',ctx :commands .Context ):
        super ().__init__ ()
        self .parent_cog =parent_cog 
        self .ctx =ctx 

    async def on_submit (self ,interaction :discord .Interaction ):
        user_id =interaction .user .id 
        user_record =self .parent_cog .pending_otp .get (user_id )
        if not user_record :
            error_embed =discord .Embed (
            title ="**Missing User Data**",
            description ="We have no record of your request. Please try again later or contact Lumen Support Team at https://discord.gg/lumenreport.",
            color =discord .Color .red ()
            )
            return await interaction .response .send_message (embed =error_embed ,ephemeral =True )

        new_password_value =self .new_password .value .strip ()


        result =update_password (user_id ,new_password_value ,db_dir =self .parent_cog .db_dir )
        if isinstance (result ,dict )and "error"in result :
            error_embed =discord .Embed (
            title ="**Password Update Failed**",
            description =result ["error"],
            color =discord .Color .red ()
            )
            return await interaction .response .send_message (embed =error_embed ,ephemeral =True )


        await self .parent_cog .edit_embed_final (interaction ,user_record .get ("email","N/A"))




class PreResetPasswordCog (commands .Cog ):
    """Cog to manage the password-reset flow by editing a single DM embed."""

    def __init__ (self ,bot ):
        self .bot =bot 
        self .pending_otp ={}
        self .active_messages ={}

        self .email_accounts =[
        {"email":"lumenbot1@gmail.com","password":"morm ucax hnrt jhug"},
        {"email":"lumenbot3@gmail.com","password":"nxiq hdhe uiig ffmg"},
        {"email":"lumenbot4@gmail.com","password":"phlp nebh pgam lqcl"},
        ]
        self .db_dir ='credentialsdatabase'

    @commands .command (name ="forgotpassword")
    async def reset_password (self ,ctx ):

        await ctx .message .delete ()


        first_embed =discord .Embed (
        title ="**Forgot Password Request**",
        description =(
        "Click the button below to enter your Recovery Email.\n\n"
        "**__Note__**:\n"
        "1. Ensure you have provided the correct email to avoid any further delays.\n"
        "2. This is a secure process to help reset your password safely.\n\n"
        "**__Precautions__**:\n"
        "-# 1. **Do not share your OTP** with anyone.\n"
        "-# 2. **Do not share your Recovery Email** with anyone.\n"
        "-# 3. Ensure you are following the official instructions to avoid phishing attempts.\n"
        "-# 4. Always verify the source of this request before proceeding.\n\n"
        "If you did not request this, **report immediately** to [Lumen Support Server](https://discord.gg/lumenreport)."
        ),
        color =0x000001 
        )
        first_embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png"
        )


        first_view =discord .ui .View (timeout =None )
        enter_email_button =discord .ui .Button (
        label ="Enter Recovery Email",
        style =discord .ButtonStyle .secondary 
        )

        async def enter_email_callback (interaction :discord .Interaction ):

            if interaction .user !=ctx .author :
                not_your_button_embed =discord .Embed (
                title ="Not Your Button!",
                description ="This button is specifically for the user who started the process.",
                color =discord .Color .red ()
                )
                return await interaction .response .send_message (embed =not_your_button_embed ,ephemeral =True )
            modal =EmailModal (parent_cog =self ,ctx =ctx )
            await interaction .response .send_modal (modal )

        enter_email_button .callback =enter_email_callback 
        first_view .add_item (enter_email_button )


        try :
            dm_message =await ctx .author .send (embed =first_embed ,view =first_view )
            self .active_messages [ctx .author .id ]=dm_message 
            success_embed =discord .Embed (
            title ="**Password Reset**",
            description ="I've sent you a **DM** with the instructions to reset your password.",
            color =0x000001 
            )
            await ctx .send (embed =success_embed )
        except discord .Forbidden :
            error_embed =discord .Embed (
            title ="**I could not DM you**",
            description ="I couldn't DM you! Please enable your DMs or contact an admin.",
            color =0xff0000 
            )
            await ctx .send (embed =error_embed )

    async def edit_embed_sending_otp (self ,interaction :discord .Interaction ,email :str ):
        """Edits the DM embed to show that the OTP is being sent."""
        user_id =interaction .user .id 
        message =self .active_messages .get (user_id )
        if not message :
            return await interaction .followup .send (
            "No active message found. Please restart the password reset flow.",
            ephemeral =True 
            )
        sending_embed =discord .Embed (
        title ="Sending OTP...",
        description =f"Please wait. We're sending an OTP to **{email }**...",
        color =0x000001 
        )
        await message .edit (embed =sending_embed ,view =None )

    async def edit_embed_step_2 (self ,interaction :discord .Interaction ,email :str ):
        """Edits the embed to prompt the user to enter the OTP."""
        user_id =interaction .user .id 
        message =self .active_messages .get (user_id )
        if not message :
            return await interaction .followup .send (
            "Internal error: no active message found. Please restart.",
            ephemeral =True 
            )
        second_embed =discord .Embed (
        title ="**Forgot Password Request**",
        description =(
        f"We have sent an OTP to your registered email address: **{email }**.\n\n"
        "**__Action Required__**:\n"
        "1. Click the button below to enter your OTP.\n"
        "2. Ensure you enter the OTP promptly to avoid expiration.\n\n"
        "**__Precautions__**:\n"
        "-# 1. Do not share your OTP with anyone.\n"
        "-# 2. Verify the email was sent from our official address.\n"
        "-# 3. If you do not see the email, check your **Spam** or **Junk** folder.\n"
        "-# 4. For any concerns, contact our support team immediately."
        ),
        color =0x000001 
        )
        second_embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png"
        )
        step2_view =discord .ui .View (timeout =None )
        enter_otp_button =discord .ui .Button (
        label ="ENTER OTP",
        style =discord .ButtonStyle .secondary 
        )

        async def enter_otp_callback (btn_interaction :discord .Interaction ):
            if btn_interaction .user .id !=user_id :
                return await btn_interaction .response .send_message ("This button isn't for you.",ephemeral =True )
            if user_id not in self .pending_otp :
                err_embed =discord .Embed (
                title ="**No Pending OTP**",
                description ="No OTP verification is currently pending. Please restart.",
                color =discord .Color .red ()
                )
                return await btn_interaction .response .send_message (embed =err_embed ,ephemeral =True )
            otp_modal =OTPModal (parent_cog =self ,ctx =None )
            await btn_interaction .response .send_modal (otp_modal )

        enter_otp_button .callback =enter_otp_callback 
        step2_view .add_item (enter_otp_button )
        await message .edit (embed =second_embed ,view =step2_view )
        await interaction .followup .send (
        f"Recovery email **{email }** verified. Next, enter the OTP.",ephemeral =True 
        )

    async def edit_embed_step_3 (self ,interaction :discord .Interaction ):
        """Edits the embed to prompt the user to set a new password."""
        user_id =interaction .user .id 
        message =self .active_messages .get (user_id )
        if not message :
            return await interaction .response .send_message (
            "No active message found. Please restart.",ephemeral =True 
            )
        third_embed =discord .Embed (
        title ="**__Forgot Password__**",
        description =(
        "Great! You’re almost there.\n\n"
        "**__Next Action__**:\n"
        "1. Click the button below to set your new password.\n"
        "2. Ensure your new password is strong, unique, and difficult to guess.\n\n"
        "**__Password Tips__**:\n"
        "- Use a mix of uppercase, lowercase, numbers, and special characters.\n"
        "- Avoid using easily guessable info.\n"
        "- Make sure this password is different from previous ones.\n\n"
        "**__Precautions__**:\n"
        "1. Do not share your new password with anyone.\n"
        "2. If you face any issues, contact our support team immediately.\n"
        "3. Always ensure you are on the official platform while setting your password."
        ),
        color =0x000001 
        )
        third_embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png"
        )
        step3_view =discord .ui .View (timeout =None )
        enter_new_pass_button =discord .ui .Button (
        label ="Enter New Password",
        style =discord .ButtonStyle .secondary 
        )

        async def enter_new_pass_callback (btn_interaction :discord .Interaction ):
            if btn_interaction .user .id not in self .pending_otp :
                err_embed =discord .Embed (
                title ="**Missing Information**",
                description ="We have no record of your email or OTP. Please restart the process.",
                color =discord .Color .red ()
                )
                return await btn_interaction .response .send_message (embed =err_embed ,ephemeral =True )
            new_pass_modal =NewPasswordModal (parent_cog =self ,ctx =None )
            await btn_interaction .response .send_modal (new_pass_modal )

        enter_new_pass_button .callback =enter_new_pass_callback 
        step3_view .add_item (enter_new_pass_button )
        await message .edit (embed =third_embed ,view =step3_view )
        await interaction .response .send_message (
        "OTP verified. Next, set your new password.",
        ephemeral =True 
        )

    async def edit_embed_final (self ,interaction :discord .Interaction ,recovery_email :str ):
        """Edits the embed to show a final success message and cleans up."""
        user_id =interaction .user .id 
        message =self .active_messages .get (user_id )
        if not message :
            return 
        final_embed =discord .Embed (
        title ="**__Password Updated Successfully!__**",
        description ="Your password has been updated. Here are the details:",
        color =0x000001 
        )
        final_embed .add_field (
        name ="**Recovery Email**",
        value =recovery_email ,
        inline =False 
        )
        final_embed .add_field (
        name ="**__Precautions__**",
        value =(
        "1. **Do not share your password** with anyone.\n"
        "2. **Use a strong, unique password** each time.\n"
        "3. **Enable 2FA** whenever possible.\n"
        "4. If you did not perform this, contact support immediately."
        ),
        inline =False 
        )
        final_embed .set_footer (text ="Lumen Security Team")
        view =SupportServerButton ()
        await message .edit (embed =final_embed ,view =view )
        await interaction .response .send_message (
        "Password updated successfully. Check the final details in the DM embed.",
        ephemeral =True 
        )

        self .active_messages .pop (user_id ,None )
        self .pending_otp .pop (user_id ,None )

async def setup (bot ):
    """Cog setup."""
    await bot .add_cog (PreResetPasswordCog (bot ))
