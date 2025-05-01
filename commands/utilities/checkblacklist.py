import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 
import sqlite3 
from config import GENERAL_STAFF_ROLE 

from functions .blacklist .db_utils import get_all_blacklist_db_connections 

class CheckBlacklist (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command ()
    async def checkblacklist (self ,ctx ,user :discord .User =None ):
        """
        Check if a user is blacklisted across multiple databases.
        Usage: +listbl [user] (if no user is provided, checks the author's status)
        """
        if not user :
            user =ctx .author 


        if user !=ctx .author and GENERAL_STAFF_ROLE not in [role .id for role in ctx .author .roles ]:
            embed =discord .Embed (
            title ="Permission Denied",
            description ="You can only check your own blacklist status.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
            return 

        user_id =str (user .id )

        connections =get_all_blacklist_db_connections ()
        is_blacklisted =False 

        try :
            for conn in connections :
                cursor =conn .cursor ()
                cursor .execute ('SELECT blacklist_status FROM blacklists WHERE user_id = ?',(user_id ,))
                result =cursor .fetchone ()
                if result and result [0 ]=='yes':
                    is_blacklisted =True 
                    break 


            embed =discord .Embed (title ="**Blacklist Status**",color =discord .Color .from_str ("#ffb03b"))
            embed .add_field (name ="Checked User",value =f"{user .mention } ({user .display_name })",inline =False )

            if is_blacklisted :
                embed .add_field (name ="Status",value ="The user is currently blacklisted.",inline =False )
                embed .color =discord .Color .from_str ("#ff0000")
            else :
                embed .add_field (name ="Status",value ="The user is not blacklisted.",inline =False )
                embed .color =discord .Color .from_str ("#000001")

            await ctx .send (embed =embed )

        except sqlite3 .Error as e :
            embed =discord .Embed (
            title ="Error",
            description ="An error occurred while checking the blacklist status.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =embed )
            print (f"Database error: {e }")

        finally :

            for conn in connections :
                conn .close ()

    @checkblacklist .error 
    async def profile_prefix_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):
            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =(f"You're on cooldown! Please try again in **{error .retry_after :.1f} seconds**."),
            color =0xff0000 ,
            timestamp =discord .utils .utcnow ()
            )
            cooldown_embed .set_footer (text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :
            raise error 

async def setup (bot ):
    await bot .add_cog (CheckBlacklist (bot ))
