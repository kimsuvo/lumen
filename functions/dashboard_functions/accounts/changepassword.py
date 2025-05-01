

import discord 
from discord import Embed 
from datetime import datetime 
import pytz 


from functions .password_functions .changepassword_functions import is_user_registered ,ChangePasswordView 

async def initiate_change_password (interaction :discord .Interaction ):
    """
    This function is called when a user clicks the Change Password button in the dashboard.
    It replicates the functionality of the changepassword command by checking if the user is
    registered, sending a DM with instructions and an interactive view, and confirming the action.
    """

    if not is_user_registered (interaction .user .id ):
        embed =Embed (
        title ="**Registration Required**",
        description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this functionality.",
        color =0xFF0000 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )
        return 


    kolkata_tz =pytz .timezone ("Asia/Kolkata")
    current_time_kolkata =datetime .now (kolkata_tz )


    embed =Embed (
    title ="**Manage Your Password**",
    description =(
    "Choose an option below to **update** or **reset** your password securely.\n\n"
    "**__Precautions__**:\n"
    "-# 1. **Do not share your password** with anyone.\n"
    "-# 2. Ensure your password is **unique** and not used elsewhere.\n"
    "-# 3. Use a combination of **letters, numbers, and special characters** for better security.\n"
    "-# 4. **Avoid clicking on suspicious links** or providing your credentials on untrusted websites.\n\n"
    "**__Your security is our priority!__**\n"
    "If you didn’t request a password change, **report immediately** to [Lumen Support Server](https://discord.gg/lumenbot)."
    ),
    color =0x000001 
    )
    embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")
    embed .set_footer (text ="For security reasons, this interaction is private.")
    embed .timestamp =current_time_kolkata 


    view =ChangePasswordView (interaction .client )

    try :

        await interaction .user .send (embed =embed ,view =view )
        confirmation_embed =Embed (
        title ="**Password Change Request**",
        description ="Please check your DMs for password management options.",
        color =0x000001 
        )
        await interaction .response .send_message (embed =confirmation_embed ,ephemeral =True )
    except discord .Forbidden :
        error_embed =Embed (
        title ="Error",
        description ="I couldn't send you a DM. Please enable DMs and try again.",
        color =0xff0000 
        )
        await interaction .response .send_message (embed =error_embed ,ephemeral =True )
