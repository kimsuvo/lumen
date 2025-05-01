import sqlite3 
import discord 
from discord .ext import commands 
from datetime import datetime 
import pytz 
from config import REPORT_STAFF_ROLE ,BLACKLIST_CHANNEL_ID 
import os 
import requests 

from functions .blacklist .db_utils import get_blacklist_db ,get_image_db 

class AddBlacklist (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .blacklist_db_dir ="blacklistsdatabase"
        self .image_db_dir ="imagedatabase"
        os .makedirs (self .blacklist_db_dir ,exist_ok =True )
        os .makedirs (self .image_db_dir ,exist_ok =True )

    @commands .command ()
    @commands .check (lambda ctx :any (role .id in REPORT_STAFF_ROLE for role in ctx .author .roles ))
    async def blacklist (self ,ctx ,user :discord .User ,*,reason :str ):
        """
        Blacklist a user.
        Usage: +blacklist <user> <reason>
        """
        user_id =str (user .id )


        processing_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Blacklisting User...**",
        color =0x000001 
        )
        processing_message =await ctx .send (embed =processing_embed )

        try :

            conn ,cursor =get_blacklist_db (user_id ,db_dir =self .blacklist_db_dir )


            cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(user_id ,))
            if cursor .fetchone ():
                final_embed =discord .Embed (
                title ="**Blacklist Failed**",
                description =f"User {user .mention } is already blacklisted.",
                color =0x000001 
                )
                await processing_message .edit (embed =final_embed )
                conn .close ()
                return 


            cursor .execute ("INSERT INTO blacklists (user_id, blacklist_status) VALUES (?, ?)",(user_id ,'yes'))
            conn .commit ()
            conn .close ()


            img_conn ,img_cursor =get_image_db (user_id ,db_dir =self .image_db_dir )
            img_cursor .execute ("SELECT * FROM imagethumbnail WHERE user_id = ?",(user_id ,))
            if img_cursor .fetchone ():
                img_cursor .execute (
                "UPDATE imagethumbnail SET image = ?, thumbnail = ?, DWC = ? WHERE user_id = ?",
                (
                'https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless',
                'https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?format=webp&quality=lossless&width=671&height=671',
                'yes',
                user_id 
                )
                )
            else :
                img_cursor .execute (
                "INSERT INTO imagethumbnail (user_id, image, thumbnail, DWC) VALUES (?, ?, ?, ?)",
                (
                user_id ,
                'https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless',
                'https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?format=webp&quality=lossless&width=671&height=671',
                'yes'
                )
                )
            img_conn .commit ()
            img_conn .close ()


            requests .get (
            f"https://api.dezinare.com/users/add/blacklist/{user_id }",
            params ={"api_key":"TYqp12dvDYuvjF4ekI8Yd2EJIVXtRkV0"}
            )



            kolkata_tz =pytz .timezone ('Asia/Kolkata')
            timestamp =datetime .now (kolkata_tz ).strftime ("%Y-%m-%d %H:%M:%S IST")

            embed =discord .Embed (title ="**User Blacklisted**",color =discord .Color .from_str ("#ff0000"))
            embed .set_thumbnail (url =user .avatar .url if user .avatar else discord .Embed .Empty )
            embed .set_image (url ="https://media.discordapp.net/attachments/1200750312844165203/1324260202496655411/blacklistbanner.png?format=webp&quality=lossless")
            embed .add_field (name ="Blacklisted By",value =ctx .author .mention ,inline =False )
            embed .add_field (name ="Blacklisted User",value =f"{user .mention } ({user .display_name })",inline =False )
            embed .add_field (name ="Blacklisted User ID",value =user_id ,inline =False )
            embed .add_field (name ="Username",value =f"{user .name }",inline =False )
            embed .add_field (name ="Reason",value =reason ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )


            blacklist_channel =self .bot .get_channel (BLACKLIST_CHANNEL_ID )
            if blacklist_channel :
                await blacklist_channel .send (embed =embed )
            else :
                await ctx .send ("Error: Blacklist channel not found. Please check the channel ID.")


            try :
                dm_embed =discord .Embed (
                title ="You Have Been Blacklisted from using our feedback system.",
                color =discord .Color .from_str ("#ff0000")
                )
                dm_embed .set_thumbnail (
                url ="https://media.discordapp.net/attachments/1200750312844165203/1327163059751358465/blacklist_logo.png?format=webp&quality=lossless"
                )
                dm_embed .add_field (name ="Blacklisted By",value =ctx .author .mention ,inline =False )
                dm_embed .add_field (name ="Reason",value =reason ,inline =False )
                dm_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
                await user .send (embed =dm_embed )
            except discord .Forbidden :
                dm_fail_embed =discord .Embed (
                title ="DM Failed",
                description =f"Could not DM {user .mention }. They might have DMs disabled.",
                color =discord .Color .from_str ("#ffcc00")
                )
                await ctx .send (embed =dm_fail_embed )


            success_embed =discord .Embed (
            title ="<:lumen_online:1324983167538696303> **Blacklist Successful**",
            description =f"User {user .mention } has been blacklisted. Reason: {reason }",
            color =0x000001 
            )
            await processing_message .edit (embed =success_embed )

        except sqlite3 .DatabaseError as e :
            error_embed =discord .Embed (
            title ="Database Error",
            description =f"There was an error interacting with the database: {str (e )}. Please try again later.",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )

    @blacklist .error 
    async def blacklist_error (self ,ctx ,error ):
        if isinstance (error ,commands .MissingRole ):
            error_embed =discord .Embed (
            title ="Permission Denied",
            description ="You don't have the required permissions to use this command.",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )
        elif isinstance (error ,commands .MemberNotFound ):
            error_embed =discord .Embed (
            title ="User Not Found",
            description ="User not found. Please mention a valid user.",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )
        elif isinstance (error ,commands .MissingRequiredArgument ):
            error_embed =discord .Embed (
            title ="Missing Arguments",
            description ="Please provide both a user and a reason. Usage: +blacklist <user> <reason>",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )
        elif isinstance (error ,sqlite3 .DatabaseError ):
            error_embed =discord .Embed (
            title ="Database Error",
            description ="There was an error interacting with the database. Please try again later.",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )
        else :
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (AddBlacklist (bot ))
