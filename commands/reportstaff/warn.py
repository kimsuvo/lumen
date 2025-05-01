import discord 
from discord .ext import commands 
from config import REPORT_STAFF_ROLE ,WARN_CHANNEL_ID 
from functions .warnings .db_utils import DatabaseManager 


WARNINGS_DB_DIR ='warningsdatabase'
WARNINGS_DB_PREFIX ='warnings_'

class AddWarning (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .warnings_db_manager =DatabaseManager (WARNINGS_DB_DIR ,WARNINGS_DB_PREFIX )

    @commands .command (name ='warn')
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def warn (self ,ctx ,user :discord .User ,*,reason :str ):
        try :

            status_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> **Warning User**",
            description ="Adding Warning...",
            color =0xFFFF00 
            )
            status_message =await ctx .send (embed =status_embed )


            warn_id =self .warnings_db_manager .generate_unique_warn_id ()


            user_db =self .warnings_db_manager .find_user_db (user .id )
            if user_db :
                target_db =user_db 
            else :
                target_db =self .warnings_db_manager .get_db_with_space ()
                if not target_db :
                    target_db =self .warnings_db_manager .create_new_db ()


            self .warnings_db_manager .insert_warning (target_db ,user .id ,warn_id ,reason )


            embed =discord .Embed (title ="**You have been warned!**",color =0xFF0000 )
            embed .add_field (name ="Warned User",value =f"{user } ({user .mention })",inline =False )
            embed .add_field (name ="Warn ID",value =warn_id ,inline =False )
            embed .add_field (name ="Reason",value =reason ,inline =False )
            embed .add_field (name ="Warned By",value =f"{ctx .author } ({ctx .author .mention })",inline =False )
            embed .set_thumbnail (url =user .display_avatar .url )
            embed .set_image (url ="https://media.discordapp.net/attachments/1200750312844165203/1327280949964308562/youvebeenwarned.png")


            try :
                await user .send (embed =embed )
            except discord .Forbidden :
                error_embed =discord .Embed (
                title ="Error",
                description =f"Could not DM {user .mention } about their warning.",
                color =0xFF0000 
                )
                await ctx .send (embed =error_embed )


            warn_channel =self .bot .get_channel (WARN_CHANNEL_ID )
            if warn_channel :
                await warn_channel .send (embed =embed )
            else :
                error_embed =discord .Embed (
                title ="Error",
                description ="Warning channel not found.",
                color =0xFF0000 
                )
                await ctx .send (embed =error_embed )


            success_embed =discord .Embed (
            title ="<:lumen_online:1324983167538696303> **Success**",
            description =f"Warned {user .mention } successfully.",
            color =0x00FF00 
            )
            await status_message .edit (embed =success_embed )

        except commands .MissingRequiredArgument as e :
            syntax_error_embed =discord .Embed (
            title ="Syntax Error",
            description =f"Missing argument: {str (e )}",
            color =0xFF0000 
            )
            await ctx .send (embed =syntax_error_embed )

        except commands .MissingRole :
            permission_error_embed =discord .Embed (
            title ="Permission Denied",
            description ="You do not have the required role to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =permission_error_embed )

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =str (e ),
            color =0xFF0000 
            )
            await ctx .send (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (AddWarning (bot ))
