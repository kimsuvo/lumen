

import os 
import discord 
from discord import Embed ,File ,ButtonStyle ,Interaction 
from discord .ext import commands 
from discord .ui import Button ,View 
import pandas as pd 
from datetime import datetime ,timedelta 
import glob 

from functions .pdf_txt_generation_functions .constants import EMBED_COLOR 
from functions .pdf_txt_generation_functions .common_functions import convert_to_timezone 
from functions .pdf_txt_generation_functions .pdf_functions import create_password_protected_pdf 
from functions .pdf_txt_generation_functions .feedback_functions import fetch_feedback_data 
from functions .register_functions .registration_functions import is_user_registered 
from functions .premium_functions .premium_user_functions import is_user_premium 

















class PreFeedbackDoc (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ='getfeedback')
    @commands .cooldown (1 ,1 ,commands .BucketType .user )
    async def getfeedback (self ,ctx ,days :str =None ):
        """
        Retrieves feedback for the user from all feedback DBs for a given number of days or 'all'.
        Provides two options via buttons:
         - Request TXT (no premium required)
         - Request PDF (premium required)
        """

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        if not days :
            error_embed =Embed (
            title ="**Missing Arguments**",
            description ="You must specify either the number of days or 'all'.\n"
            "Example: `+getfeedback 7` or `+getfeedback all`",
            color =0xFF0000 
            )
            error_embed .set_footer (text =f"Requested by {ctx .author }")
            await ctx .send (embed =error_embed ,delete_after =10 )
            return 

        days =days .lower ().strip ()
        if days !="all":
            try :
                days_int =int (days )
            except ValueError :
                error_embed =Embed (
                title ="**Invalid Argument**",
                description ="Please specify either `'all'` or a number of days (e.g. `7`) up to 365.",
                color =0xFF0000 
                )
                error_embed .set_footer (text =f"Requested by {ctx .author }")
                await ctx .send (embed =error_embed ,delete_after =10 )
                return 

            if not (1 <=days_int <=365 ):
                error_embed =Embed (
                title ="**Invalid Number of Days**",
                description ="Please specify a number of days between 1 and 365.",
                color =0xFF0000 
                )
                error_embed .set_footer (text =f"Requested by {ctx .author }")
                await ctx .send (embed =error_embed ,delete_after =10 )
                return 
        else :
            days_int ="all"


        request_embed =Embed (
        title ="Select the Format You Want for Your Feedback",
        description ="Please choose **Request PDF** (premium only) or **Request TXT** (free) below.",
        color =EMBED_COLOR 
        )
        request_embed .set_footer (text =f"Requested by {ctx .author }")

        view =FeedbackFormatView (ctx ,days ,days_int )
        await ctx .send (embed =request_embed ,view =view )

    @getfeedback .error 
    async def getfeedback_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):
            cooldown_embed =Embed (
            title ="Cooldown Active",
            description =f"This command is on cooldown. Please try again in {round (error .retry_after )} seconds.",
            color =discord .Color .red ()
            )
            cooldown_embed .set_footer (text =f"Requested by {ctx .author }")
            await ctx .send (embed =cooldown_embed )
        else :
            raise error 



class FeedbackFormatView (discord .ui .View ):
    """
    A custom View with two buttons: "Request PDF" and "Request TXT".
    """
    def __init__ (self ,ctx ,days_str ,days_int ):
        super ().__init__ (timeout =None )
        self .ctx =ctx 
        self .days_str =days_str 
        self .days_int =days_int 
        self .embed_msg =None 

    @discord .ui .button (label ="Request PDF",style =discord .ButtonStyle .primary )
    async def request_pdf (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        """
        Handles the logic for generating a PDF feedback report (Premium only).
        """
        if interaction .user .id !=self .ctx .author .id :
            await interaction .response .send_message (
            "You cannot use someone else's feedback buttons!",
            ephemeral =True 
            )
            return 

        if not is_user_premium (self .ctx .author .id ):
            premium_embed =discord .Embed (
            title ="**Upgrade to Lumen Premium**",
            description ="You need Lumen Premium to request a PDF report. Please upgrade to access this feature.",
            color =0xff0000 
            )
            premium_embed .set_footer (text =f"Requested by {self .ctx .author }")
            await interaction .response .edit_message (embed =premium_embed ,view =None )
            return 

        processing_embed =discord .Embed (
        title ="Gathering Feedback...",
        description =f"Please wait while we gather and generate your **PDF** feedback for the last {self .days_str } days.",
        color =0x000001 
        )
        processing_embed .set_footer (text =f"Requested by {self .ctx .author }")
        await interaction .response .edit_message (embed =processing_embed ,view =None )


        all_rows =fetch_feedback_data (self .ctx .author .id ,self .days_int )
        if all_rows is None :
            nodb_embed =discord .Embed (
            title ="No Feedback Databases Found",
            description ="No feedback databases found in the 'feedbackdatabase' directory.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =nodb_embed )
            return 

        if not all_rows :
            no_feedback_embed =discord .Embed (
            title ="No Feedback Found",
            description =f"No feedback found for the last {self .days_str } days.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =no_feedback_embed )
            return 

        processed_rows =[]
        for row in all_rows :
            row =list (row )
            if len (row )>4 :
                row [4 ]=convert_to_timezone (row [4 ])
            else :
                row .append ("Invalid Timestamp")
            processed_rows .append (row )

        import pandas as pd 
        df =pd .DataFrame (
        processed_rows ,
        columns =['Giver ID','Receiver ID','Feedback','Feedback Type','Timestamp']
        )

        user_id =self .ctx .author .id 
        username =self .ctx .author .name 
        server_name =self .ctx .guild .name if self .ctx .guild else "Direct Message"
        server_id =self .ctx .guild .id if self .ctx .guild else "DM"


        try :
            pdf_path ,password =create_password_protected_pdf (
            df ,
            user_id ,
            self .days_str ,
            username ,
            server_name ,
            server_id 
            )
        except Exception as e :
            error_embed =discord .Embed (
            title ="PDF Generation Error",
            description =f"An unexpected error occurred while generating PDF: {e }",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =error_embed )
            return 


        try :
            dm_channel =await self .ctx .author .create_dm ()
            embed =discord .Embed (
            title =f"**__Your Feedback Data for {self .days_str } Days__**",
            description =(
            "Attached is your **password-protected** PDF report.\n\n"
            "**Password Format**:\n"
            "It's simply your `User ID` + the requested days.\n\n"
            f"**Example**: If User ID is `{user_id }` and days = `{self .days_str }`, "
            f"password = `{user_id }{self .days_str }`"
            ),
            color =0x000001 
            )
            embed .add_field (name ="Requested By",value =str (self .ctx .author ),inline =False )
            embed .add_field (name ="Server Name",value =server_name ,inline =False )
            await dm_channel .send (embed =embed ,file =discord .File (pdf_path ))
            success_embed =discord .Embed (
            title ="Feedback Data Sent!",
            description =f"Your PDF feedback for the last {self .days_str } days has been sent to your DMs.",
            color =0x000001 
            )
            await interaction .edit_original_response (embed =success_embed )
        except discord .Forbidden :
            forbidden_embed =discord .Embed (
            title ="Unable to Send DM",
            description ="I couldn't send you a DM. Please enable DMs and try again.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =forbidden_embed )
        finally :
            if pdf_path and os .path .exists (pdf_path ):
                os .remove (pdf_path )

    @discord .ui .button (label ="Request TXT",style =discord .ButtonStyle .success )
    async def request_txt (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        """
        Handles the logic for generating a TXT feedback report (free version).
        """
        if interaction .user .id !=self .ctx .author .id :
            await interaction .response .send_message (
            "You cannot use someone else's feedback buttons!",
            ephemeral =True 
            )
            return 

        processing_embed =discord .Embed (
        title ="Gathering Feedback...",
        description =f"Please wait while we gather and generate your **TXT** feedback for the last {self .days_str } days.",
        color =0x000001 
        )
        processing_embed .set_footer (text =f"Requested by {self .ctx .author }")
        await interaction .response .edit_message (embed =processing_embed ,view =None )

        all_rows =fetch_feedback_data (self .ctx .author .id ,self .days_int )
        if all_rows is None :
            nodb_embed =discord .Embed (
            title ="No Feedback Databases Found",
            description ="No feedback databases found in the 'feedbackdatabase' directory.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =nodb_embed )
            return 

        if not all_rows :
            no_feedback_embed =discord .Embed (
            title ="No Feedback Found",
            description =f"No feedback found for the last {self .days_str } days.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =no_feedback_embed )
            return 

        processed_rows =[]
        for row in all_rows :
            row =list (row )
            if len (row )>4 :
                row [4 ]=convert_to_timezone (row [4 ])
            else :
                row .append ("Invalid Timestamp")
            processed_rows .append (row )

        txt_lines =[]
        txt_lines .append (f"LUMEN FEEDBACK REPORT for {self .days_str } day(s)\n")
        txt_lines .append (f"User ID: {self .ctx .author .id }\n")
        txt_lines .append (f"Username: {self .ctx .author .name }\n")
        server_name =self .ctx .guild .name if self .ctx .guild else "Direct Message"
        server_id =self .ctx .guild .id if self .ctx .guild else "DM"
        txt_lines .append (f"Requested from Server: {server_name }\n")
        txt_lines .append (f"Server ID: {server_id }\n")
        txt_lines .append (f"Total Feedback Records: {len (processed_rows )}\n")
        txt_lines .append (f"Timestamp: {datetime .now ().strftime ('%Y-%m-%d %I:%M %p')}\n\n")

        for row in processed_rows :
            txt_lines .append (f"Giver ID: {row [0 ]}\n")
            txt_lines .append (f"Feedback: {row [2 ]}\n")
            txt_lines .append (f"Feedback Type: {row [3 ]}\n")
            txt_lines .append (f"Timestamp: {row [4 ]}\n")
            txt_lines .append ("-"*50 +"\n")

        txt_filename =f"{self .ctx .author .id }_{self .days_str }_feedback.txt"
        with open (txt_filename ,"w",encoding ="utf-8")as f :
            f .writelines (txt_lines )

        try :
            dm_channel =await self .ctx .author .create_dm ()
            txt_embed =discord .Embed (
            title ="Your TXT Feedback",
            description =f"Here’s your `.txt` feedback for the last **{self .days_str }** day(s).",
            color =0x000001 
            )
            txt_embed .add_field (
            name ="Want a PDF Version?",
            value ="Upgrade to **Lumen Premium** to request a PDF format of your feedback!",
            inline =False 
            )

            from functions .premium_functions .premium_user_functions import is_user_premium 
            from discord .ui import View ,Button 
            class PremiumLinkView (View ):
                def __init__ (self ):
                    super ().__init__ ()
                    premium_button =Button (label ="Get Lumen Premium",url ="https://lumen.dezinare.com",style =discord .ButtonStyle .link )
                    self .add_item (premium_button )
            await dm_channel .send (embed =txt_embed ,file =discord .File (txt_filename ),view =PremiumLinkView ())
            success_embed =discord .Embed (
            title ="Feedback Data Sent!",
            description =f"Your TXT feedback for the last {self .days_str } days has been sent to your DMs.",
            color =0x000001 
            )
            await interaction .edit_original_response (embed =success_embed )
        except discord .Forbidden :
            forbidden_embed =discord .Embed (
            title ="Unable to Send DM",
            description ="I couldn't send you a DM. Please enable DMs and try again.",
            color =discord .Color .red ()
            )
            await interaction .edit_original_response (embed =forbidden_embed )
        finally :
            if os .path .exists (txt_filename ):
                os .remove (txt_filename )
















async def setup (bot ):
    await bot .add_cog (PreFeedbackDoc (bot ))
