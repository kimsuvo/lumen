import discord 
import requests 
from discord .ext import commands 
from discord import Embed 
from config import REPORT_STAFF_ROLE ,DWC_CHANNEL_ID 


from functions .dwc .db_utils import get_user_data ,save_user_data ,update_image_data 

class DWCStatus (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="dwc")
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def toggle_dwc (self ,ctx ,*,input_value :str =None ):
        """
        Toggles the DWC (Do Not Warrant) status for a user.
        """


        if not input_value :
            embed =Embed (
            title ="**Error**",
            description =(
            "<:lumen_dnd:1324983165554524252> Please specify a user mention, username, or user ID.\n\n"
            "**Examples:**\n"
            "`+dwc 123456789012345678` (User ID)\n"
            "`+dwc username` (Username)\n"
            "`+dwc @mention` (User mention)"
            ),
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 

        try :

            user =None 
            input_value =input_value .lower ()

            if input_value .isdigit ():

                user =await self .bot .fetch_user (int (input_value ))
            elif input_value .startswith ("<@")and input_value .endswith (">"):

                mention_id =int (input_value .strip ("<@!>"))
                user =await self .bot .fetch_user (mention_id )
            else :

                user =await self .bot .fetch_user (input_value )

            if not user :
                raise ValueError ("User not found")

        except (ValueError ,discord .NotFound ):
            embed =Embed (
            title ="**Error**",
            description =(
            "<:lumen_dnd:1324983165554524252> User not found. "
            "Please provide a valid mention, username, or user ID."
            ),
            color =0xFBB03B 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        user_data =get_user_data (user .id )

        if not user_data :

            user_data ={
            "user_id":str (user .id ),
            "thumbnail":"https://media.discordapp.net/attachments/1200750312844165203/1324643383289057300/dwc_icon.png",
            "image":"https://media.discordapp.net/attachments/1200750312844165203/1324254316483055646/dwc.png",
            "DWC":"no"
            }
            save_user_data (user_data )


        if user_data .get ("DWC","").lower ()=="yes":
            update_image_data (user .id ,"DWC","no")
            update_image_data (user .id ,"image","https://media.discordapp.net/attachments/1200750312844165203/1323958955025895454/lumen_banner.png")
            update_image_data (user .id ,"thumbnail",None )
            status ="No"
            updated_image ="Reset to the default image."


            requests .get (
            f"https://api.dezinare.com/users/remove/dwc/{user .id }",
            params ={"api_key":"TYqp12dvDYuvjF4ekI8Yd2EJIVXtRkV0"}
            )

        else :
            update_image_data (user .id ,"DWC","yes")
            update_image_data (user .id ,"image","https://media.discordapp.net/attachments/1200750312844165203/1324254316483055646/dwc.png")
            update_image_data (user .id ,"thumbnail","https://media.discordapp.net/attachments/1200750312844165203/1324643383289057300/dwc_icon.png")
            status ="Yes"
            updated_image ="Updated to the DWC image and thumbnail."


            requests .get (
            f"https://api.dezinare.com/users/add/dwc/{user .id }",
            params ={"api_key":"TYqp12dvDYuvjF4ekI8Yd2EJIVXtRkV0"}
            )


        embed =Embed (
        title ="**<:lumen_warning:1324983182583664650> DWC Status Updated**",
        description =(
        f"**User**: {user .mention }\n"
        f"**DWC Status**: {status }\n"
        f"**Image**: {updated_image }"
        ),
        color =0xFBB03B 
        )
        await ctx .send (embed =embed )


        try :
            dm_embed =Embed (
            title ="**DWC Status Update Notification**",
            description =(
            f"Hello {user .mention },\n\n"
            f"Your DWC status has been updated by **{ctx .author .mention }**.\n\n"
            f"**New Status**: `{status }`\n"
            f"**Changed By**: {ctx .author .mention }\n"
            f"**Time**: <t:{int (ctx .message .created_at .timestamp ())}:F>\n\n"
            f"We appreciate your cooperation!"
            ),
            color =0xFF0000 
            )
            dm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1324643383289057300/dwc_icon.png")
            await user .send (embed =dm_embed )
        except discord .Forbidden :

            pass 


        webhook_embed =Embed (
        title ="DWC Status Update",
        description =(
        f"**User ID**: {user .id }\n"
        f"**User Mention**: {user .mention }\n"
        f"**Username**: {user .name }\n"
        f"**DWC Status**: {status }\n"
        f"**Timestamp**: <t:{int (ctx .message .created_at .timestamp ())}:F>\n"
        f"**DWC By**: {ctx .author .mention } ({ctx .author .name })\n"
        ),
        color =0xFF0000 
        )
        webhook_embed .set_thumbnail (url =user .avatar .url )
        webhook_embed .set_image (url ="https://media.discordapp.net/attachments/1200750312844165203/1324254316483055646/dwc.png")


        dwc_channel =self .bot .get_channel (DWC_CHANNEL_ID )
        if dwc_channel :
            await dwc_channel .send (embed =webhook_embed )

async def setup (bot ):

    await bot .add_cog (DWCStatus (bot ))
