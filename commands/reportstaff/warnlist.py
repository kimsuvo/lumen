import discord 
from discord .ext import commands 
from config import REPORT_STAFF_ROLE 
from functions .warnings .db_utils import DatabaseManager 


WARNINGS_DB_DIR ='warningsdatabase'
WARNINGS_DB_PREFIX ='warnings_'

class WarnList (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .warnings_db_manager =DatabaseManager (WARNINGS_DB_DIR ,WARNINGS_DB_PREFIX )

    @commands .command (name ='warnlist')
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def warnlist (self ,ctx ,user :discord .User ):
        try :

            status_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> **Fetching Warnings**",
            description ="Searching warnings...",
            color =0x000001 
            )
            status_message =await ctx .send (embed =status_embed )


            warnings =self .warnings_db_manager .get_warnings_for_user (user .id )

            if warnings :
                embed =discord .Embed (
                title =f"**Warnings for {user }**",
                color =0x000001 
                )
                for warn_id ,reason in warnings :
                    embed .add_field (name =f"Warn ID: `{warn_id }`",value =reason ,inline =False )
                await status_message .edit (embed =embed )
            else :
                error_embed =discord .Embed (
                title ="No Warnings Found",
                description =f"No warnings found for {user .mention }.",
                color =0x000001 
                )
                await status_message .edit (embed =error_embed )

        except commands .MissingRequiredArgument as e :
            syntax_error_embed =discord .Embed (
            title ="Syntax Error",
            description =f"Missing argument: {str (e )}",
            color =0xFF0000 
            )
            await ctx .send (embed =syntax_error_embed )

        except Exception as e :
            error_embed =discord .Embed (
            title ="Error",
            description =str (e ),
            color =0xFF0000 
            )
            await ctx .send (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (WarnList (bot ))
