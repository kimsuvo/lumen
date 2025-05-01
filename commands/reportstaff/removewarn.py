import discord 
from discord .ext import commands 
from config import REPORT_STAFF_ROLE 
from functions .warnings .db_utils import DatabaseManager 


WARNINGS_DB_DIR ='warningsdatabase'
WARNINGS_DB_PREFIX ='warnings_'

class RemoveWarn (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .warnings_db_manager =DatabaseManager (WARNINGS_DB_DIR ,WARNINGS_DB_PREFIX )

    @commands .command (name ='warnremove')
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def warnremove (self ,ctx ,warn_id :str ):
        try :

            status_embed =discord .Embed (
            title ="<a:lumen_loading:1326260453260656735> **Processing Warning Removal**",
            description ="Removing Warning...",
            color =0xFFFF00 
            )
            status_message =await ctx .send (embed =status_embed )


            found =self .warnings_db_manager .remove_warning (warn_id )

            if found :
                success_embed =discord .Embed (
                title ="<:lumen_online:1324983167538696303> **Success**",
                description =f"Warning with ID {warn_id } has been removed from all databases.",
                color =0x00FF00 
                )
                await status_message .edit (embed =success_embed )
            else :
                error_embed =discord .Embed (
                title ="Error",
                description =f"No warning found with ID {warn_id } in any database.",
                color =0xFF0000 
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
    await bot .add_cog (RemoveWarn (bot ))
