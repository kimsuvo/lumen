

import discord 
from discord .ext import commands 
from datetime import datetime 
import pytz 
import re 
import unicodedata 

from config import (
PENDING_FEEDBACK_CHANNEL_ID ,
PREMIUM_PENDING_FEEDBACK_CHANNEL_ID ,
FB_BATCH_1_PING ,
FB_BATCH_2_PING ,
FB_BATCH_3_PING ,
FB_BATCH_4_PING ,
FB_BATCH_5_PING ,
FB_BATCH_6_PING ,
FB_BATCH_7_PING ,
FB_BATCH_8_PING ,
FB_BATCH_9_PING ,
FB_BATCH_10_PING ,
PREMIUM_FB_BATCH_1_PING ,
PREMIUM_FB_BATCH_2_PING ,
PREMIUM_FB_BATCH_3_PING ,
PREMIUM_FB_BATCH_4_PING ,
PREMIUM_FB_BATCH_5_PING ,
PREMIUM_FB_BATCH_6_PING ,
PREMIUM_FB_BATCH_7_PING ,
PREMIUM_FB_BATCH_8_PING ,
PREMIUM_FB_BATCH_9_PING ,
PREMIUM_FB_BATCH_10_PING ,
)

INDIA_TZ =pytz .timezone ("Asia/Kolkata")


from functions .feedback_functions .negfb_database_functions import (
user_exists_in_ban_db ,
is_user_premium ,
load_current_db_index ,
save_current_db_index ,
load_current_premium_db_index ,
save_current_premium_db_index ,
append_pending_feedback ,
append_premium_pending_feedback 
)
from functions .register_functions .registration_functions import is_user_registered 
from functions .feedback_functions .neg_feedback_functions import (
can_vouch_again ,
is_user_blacklisted ,
generate_vouch_number 
)

class PreNegativeFeedbackCog (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="negativefeedback",aliases =["nrep","nvouch"])
    async def negative_feedback_prefix (self ,ctx ,user :discord .User =None ,*,feedback :str =None ):

        if not user :
            embed =discord .Embed (
            title ="**Error**",
            description ="You must mention a user to give feedback to, and provide feedback text.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if not feedback :
            embed =discord .Embed (
            title ="**Error**",
            description ="You must mention a user and provide feedback.\n\n**Correct Usage:** +rep @user Your feedback here",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 


        if len (feedback )<15 :
            embed =discord .Embed (
            title ="**Error**",
            description ="Feedback must be at least 15 characters long.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if len (feedback )>100 :
            embed =discord .Embed (
            title ="**Error**",
            description ="Feedback must not exceed 100 characters.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        allowed_symbols ={"|","(",")","[","]","{","}",".",",","•","!",":","-","+",'"',"%","/","\\","?","<",">","~"}
        for char in feedback :
            category =unicodedata .category (char )
            if category .startswith ("S")and category !="Sc"and char not in allowed_symbols :
                embed =discord .Embed (
                title ="**Error**",
                description ="Feedback must not contain any emoji or symbol characters (except currency symbols).",
                color =0xFF0000 
                )
                error_message =await ctx .send (embed =embed )
                await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
                await error_message .delete (delay =5 )
                return 


        if ctx .author .id ==user .id :
            embed =discord .Embed (
            title ="**Error**",
            description ="You cannot give feedback to yourself.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if user .bot :
            embed =discord .Embed (
            title ="**Error**",
            description ="You cannot give feedback to a bot.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 


        if is_user_blacklisted (ctx .author .id ):
            embed =discord .Embed (
            title ="**Error**",
            description ="You are blacklisted and cannot use this command.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if is_user_blacklisted (user .id ):
            embed =discord .Embed (
            title ="**User Blacklisted**",
            description =f"User `{user .name }` is blacklisted and cannot receive feedback.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 

        if not can_vouch_again (ctx .author .id ):
            embed =discord .Embed (
            title ="**Error**",
            description ="You must wait at least 10 seconds before giving another vouch.",
            color =0xFF0000 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )
            return 


        if not is_user_registered (user .id ):
            embed =discord .Embed (
            title ="**The user isn't registered with Lumen!**",
            description =f"The user `{user .name }` is not registered with Lumen.",
            color =0x000001 
            )
            error_message =await ctx .send (embed =embed )
            await ctx .message .add_reaction ("<:lumen_dnd:1324983165554524252>")
            await error_message .delete (delay =5 )


            try :
                dm_embed =discord .Embed (
                title ="**Feedback Notification System**",
                description =(
                f"Hello! You’ve just received feedback from **{ctx .author .name }**.\n\n"
                "**Unfortunately, you're not registered with us yet!**\n"
                "You cannot view or manage your feedback until you create an account.\n\n"
                "Click **Register Now** below to get started."
                ),
                color =0x000001 
                )
                dm_embed .set_thumbnail (url ="https://example.com/yourimage.png")
                dm_embed .set_footer (text ="LumenBot Feedback System | Secure and Reliable")
                view =discord .ui .View ()
                from functions .register_functions .registration_functions import RegisterButton 
                view .add_item (RegisterButton (authorized_user =user ))
                await user .send (embed =dm_embed ,view =view )
            except discord .Forbidden :
                await ctx .send (f"Could not send a DM to <@{user .id }> (DMs are closed).")
            return 


        vouch_number =generate_vouch_number ()
        pending_feedback ={
        "vouch_number":vouch_number ,
        "giver_id":str (ctx .author .id ),
        "receiver_id":str (user .id ),
        "feedback":feedback ,
        "timestamp":datetime .now (INDIA_TZ ).strftime ("%Y-%m-%d %H:%M:%S"),
        "type":"negative"
        }

        if is_user_premium (user .id ):
            current_index =load_current_premium_db_index ()
            batch_number =(current_index %10 )+1 
            save_current_premium_db_index (current_index +1 )
            append_premium_pending_feedback (pending_feedback ,batch_number )
        else :
            current_index =load_current_db_index ()
            batch_number =(current_index %10 )+1 
            save_current_db_index (current_index +1 )
            append_pending_feedback (pending_feedback ,batch_number )


        embed =discord .Embed (
        title ="**Feedback Submitted**",
        description =(
        f"Your feedback for `{user .name }` has been successfully submitted.\n"
        "-# It will be reviewed shortly."
        ),
        color =0x000001 ,
        )
        confirmation_message =await ctx .send (embed =embed )
        await confirmation_message .delete (delay =10 )
        await ctx .message .add_reaction ("<:lumen_online:1324983167538696303>")


        try :
            dm_embed =discord .Embed (
            title ="**Feedback Received**",
            description =(
            f"<:lumen_dnd:1324983165554524252> You have received a negative feedback from `{ctx .author .name }`.\n"
            f"The ID of this feedback is `{vouch_number }`.\n"
            "-# Once approved, it will be added to your profile."
            ),
            color =0x000001 
            )
            await user .send (embed =dm_embed )
        except discord .Forbidden :
            print (f"Could not send DM to {user .name } ({user .id }).")


        async def send_feedback_to_channel ():
            if is_user_premium (user .id ):

                pending_channel =ctx .guild .get_channel (PREMIUM_PENDING_FEEDBACK_CHANNEL_ID )or await ctx .bot .fetch_channel (PREMIUM_PENDING_FEEDBACK_CHANNEL_ID )
                if not pending_channel :
                    print ("Premium pending feedback channel not found.")
                    return 

                embed_to_send =discord .Embed (
                title ="New Negative Feedback Received (Premium)",
                description =(
                f"-# **Feedback ID:** {vouch_number }\n"
                f"-# **Giver:** <@{ctx .author .id }>\n"
                f"-# **Receiver:** <@{user .id }>\n"
                f"-# **Feedback:** {feedback }\n"
                f"-# **Timestamp:** {datetime .now (INDIA_TZ ).strftime ('%Y-%m-%d %H:%M:%S')}"
                ),
                color =0x000001 ,
                timestamp =datetime .now (INDIA_TZ )
                )
                embed_to_send .add_field (name ="BATCH",value =str (batch_number ),inline =False )
                embed_to_send .set_footer (text ="Feedback System Notification")

                ping_role_id =getattr (__import__ ("config"),f"PREMIUM_FB_BATCH_{batch_number }_PING",None )
                ping_text =f"<@&{ping_role_id }>"if ping_role_id else ""
                await pending_channel .send (content =ping_text ,embed =embed_to_send )
            else :

                pending_channel =ctx .guild .get_channel (PENDING_FEEDBACK_CHANNEL_ID )or await ctx .bot .fetch_channel (PENDING_FEEDBACK_CHANNEL_ID )
                if not pending_channel :
                    print ("Pending feedback channel not found.")
                    return 

                embed_to_send =discord .Embed (
                title ="New Negative Feedback Received",
                description =(
                f"-# **Feedback ID:** {vouch_number }\n"
                f"-# **Giver:** <@{ctx .author .id }>\n"
                f"-# **Receiver:** <@{user .id }>\n"
                f"-# **Feedback:** {feedback }\n"
                f"-# **Timestamp:** {datetime .now (INDIA_TZ ).strftime ('%Y-%m-%d %H:%M:%S')}"
                ),
                color =0x000001 ,
                timestamp =datetime .now (INDIA_TZ )
                )
                embed_to_send .add_field (name ="BATCH",value =str (batch_number ),inline =False )
                embed_to_send .set_footer (text ="Feedback System Notification")

                ping_role_id =getattr (__import__ ("config"),f"FB_BATCH_{batch_number }_PING",None )
                ping_text =f"<@&{ping_role_id }>"if ping_role_id else ""
                await pending_channel .send (content =ping_text ,embed =embed_to_send )

        await send_feedback_to_channel ()


async def setup (bot ):
    await bot .add_cog (PreNegativeFeedbackCog (bot ))
