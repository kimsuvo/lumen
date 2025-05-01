import discord 
import requests 
from discord .ext import commands 
from discord import Embed 
from config import REPORT_STAFF_ROLE 

ADMIN_API_KEY ="FtlWGL5PTJNNlZ_-5J_Pug"
API_BASE_URL ="https://api.dezinare.com"

class CheckUser (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="checkuser")
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def check_user_status (self ,ctx ,*,input_value :str =None ):
        """
        Checks if the user is marked DWC or blacklisted in the external API.
        Usage: +checkuser @mention / user_id / username
        """

        if not input_value :
            embed =Embed (
            title ="**Error**",
            description =(
            "Please specify a user mention, user ID, or username.\n\n"
            "**Examples:**\n"
            "`+checkuser 123456789012345678` (User ID)\n"
            "`+checkuser username` (Username)\n"
            "`+checkuser @mention` (User mention)"
            ),
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        user =None 
        input_value =input_value .lower ()

        try :
            if input_value .isdigit ():
                user =await self .bot .fetch_user (int (input_value ))
            elif input_value .startswith ("<@")and input_value .endswith (">"):
                mention_id =int (input_value .strip ("<@!>"))
                user =await self .bot .fetch_user (mention_id )
            else :

                user =await self .bot .fetch_user (input_value )
        except discord .NotFound :
            user =None 

        if not user :

            embed =Embed (
            title ="**Error**",
            description ="User not found. Please provide a valid mention, username, or user ID.",
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 



        try :
            url =f"{API_BASE_URL }/userstatus/{user .id }"

            response =requests .get (url ,params ={"api_key":ADMIN_API_KEY },timeout =10 )
            if response .status_code !=200 :
                raise ValueError (f"HTTP {response .status_code }: {response .text }")

            data =response .json ()
            dwc_status =data .get ("dwc_status","unknown")
            blacklist_status =data .get ("blacklist_status","unknown")

            embed =Embed (
            title ="**User Status Check**",
            description =(
            f"**User**: {user .mention }\n"
            f"**DWC Status**: {dwc_status }\n"
            f"**Blacklist Status**: {blacklist_status }"
            ),
            color =0x00FF00 
            )
            await ctx .send (embed =embed )

        except Exception as e :
            error_embed =Embed (
            title ="**Error**",
            description =f"Failed to get user status from API. Error: {e }",
            color =0xFF0000 
            )
            await ctx .send (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (CheckUser (bot ))
