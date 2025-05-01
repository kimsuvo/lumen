import discord 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
from config import BLACKLIST_CHANNEL_ID ,REPORT_STAFF_ROLE 

import requests 
from functions .blacklist .db_utils import get_blacklist_db ,find_user_blacklist_db ,get_image_db ,find_user_image_db 

class RemoveBlacklist (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def removeblacklist (self ,ctx ,user :discord .User =None ):
        """Unblacklist a user."""
        if user is None :
            await ctx .send ("Please mention a user to remove from the blacklist.")
            return 

        user_id =str (user .id )
        processing_embed =discord .Embed (title ="Removing Blacklist...",color =discord .Color .from_str ("#ffcc00"))
        processing_message =await ctx .send (embed =processing_embed )


        bl_conn ,bl_cursor =find_user_blacklist_db (user_id )
        if not bl_conn :
            final_embed =discord .Embed (
            title ="Unblacklist Failed",
            description =f"User {user .mention } is not blacklisted.",
            color =discord .Color .from_str ("#ff0000")
            )
            await processing_message .edit (embed =final_embed )
            return 

        try :

            bl_cursor .execute ("DELETE FROM blacklists WHERE user_id = ?",(user_id ,))
            bl_conn .commit ()
            bl_conn .close ()


            img_conn ,img_cursor =find_user_image_db (user_id )
            if not img_conn :
                img_conn ,img_cursor =get_image_db (user_id )
            img_cursor .execute (
            "REPLACE INTO imagethumbnail (user_id, image, thumbnail, DWC) VALUES (?, ?, ?, ?)",
            (user_id ,
            'https://media.discordapp.net/attachments/1200750312844165203/1323958955025895454/lumen_banner.png?format=webp',
            'https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?format=webp',
            'no')
            )
            img_conn .commit ()
            img_conn .close ()


            requests .get (
            f"https://api.dezinare.com/users/remove/blacklist/{user_id }",
            params ={"api_key":"TYqp12dvDYuvjF4ekI8Yd2EJIVXtRkV0"}
            )


            kolkata_tz =pytz .timezone ('Asia/Kolkata')
            timestamp =datetime .now (kolkata_tz ).strftime ("%Y-%m-%d %H:%M:%S IST")

            embed =discord .Embed (title ="User Unblacklisted",color =discord .Color .from_str ("#58f25c"))
            embed .set_thumbnail (url =user .display_avatar .url )
            embed .set_image (url ="https://media.discordapp.net/attachments/1322554604885512222/1327161454079639563/blremoved.png?format=webp")
            embed .add_field (name ="Unblacklisted By",value =ctx .author .mention ,inline =False )
            embed .add_field (name ="User ID",value =user_id ,inline =False )
            embed .add_field (name ="Timestamp",value =timestamp ,inline =False )

            blacklist_channel =self .bot .get_channel (BLACKLIST_CHANNEL_ID )
            if blacklist_channel :
                await blacklist_channel .send (embed =embed )


            try :
                dm_embed =discord .Embed (
                title ="You Have Been Unblacklisted! You can now start using our feedback system.",
                color =discord .Color .from_str ("#ffcc00")
                )
                dm_embed .set_thumbnail (url =user .display_avatar .url )
                dm_embed .add_field (name ="Unblacklisted By",value =ctx .author .mention ,inline =False )
                dm_embed .add_field (name ="Username",value =f"{user .name }",inline =False )
                dm_embed .add_field (name ="Display Name",value =f"{user .display_name }",inline =False )
                dm_embed .add_field (name ="Timestamp",value =timestamp ,inline =False )
                await user .send (embed =dm_embed )
            except discord .Forbidden :
                pass 

            success_embed =discord .Embed (
            title ="<:lumen_online:1324983167538696303> **Blacklist Removal Successful**",
            description =f"User {user .mention } has been unblacklisted.",
            color =discord .Color .from_str ("#58f25c")
            )
            await processing_message .edit (embed =success_embed )

        except sqlite3 .DatabaseError as e :
            error_embed =discord .Embed (
            title ="Database Error",
            description =f"Database error occurred: {str (e )}",
            color =discord .Color .from_str ("#ff0000")
            )
            await ctx .send (embed =error_embed )

    @removeblacklist .error 
    async def unblacklist_error (self ,ctx ,error ):
        """Handles errors for the removeblacklist command."""
        error_embed =discord .Embed (color =discord .Color .from_str ("#ff0000"))
        if isinstance (error ,commands .MissingRole ):
            error_embed .title ="Permission Denied"
            error_embed .description ="You don't have the required permissions to use this command."
        elif isinstance (error ,commands .MemberNotFound ):
            error_embed .title ="User Not Found"
            error_embed .description ="Please mention a valid user."
        elif isinstance (error ,sqlite3 .DatabaseError ):
            error_embed .title ="Database Error"
            error_embed .description ="An error occurred while interacting with the database."
        else :
            error_embed .title ="Unexpected Error"
            error_embed .description ="An unknown error occurred. Please try again later."
        await ctx .send (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (RemoveBlacklist (bot ))
