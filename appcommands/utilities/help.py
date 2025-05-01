import discord 
from discord import app_commands 
from discord .ext import commands 
from datetime import datetime 
from pytz import timezone 

class Help (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @app_commands .command (name ="help",description ="Show Lumen Bot command help.")
    async def help (self ,interaction :discord .Interaction ):
        embed =discord .Embed (
        title ="**__Lumen Command Help__**",
        description =(
        "**Welcome to the Lumen Bot!**\n\n"
        "**__General__**\n"
        "-# Basic interaction commands (e.g., giving positive or negative feedback).\n\n"
        "**__Profile__**\n"
        "-# Commands to manage and view user profiles, top charts, and searches.\n\n"
        "**__Account__**\n"
        "-# Manage your account settings, passwords, recovery, and data deletion requests.\n\n"
        "**__Premium__**\n"
        "-# Exclusive commands for premium users.\n\n"
        ),
        color =0x000001 
        )
        embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png"
        )


        view =discord .ui .View (timeout =60 )
        dropdown =HelpDropdown (interaction .user )
        view .add_item (dropdown )

        await interaction .response .send_message (embed =embed ,view =view )

class HelpDropdown (discord .ui .Select ):
    def __init__ (self ,author ):
        self .author =author 
        options =[
        discord .SelectOption (
        label ="General Commands",
        description ="Basic commands like +rep, +store, +color, etc.",
        value ="general"
        ),
        discord .SelectOption (
        label ="Profile & Ranking",
        description ="Commands for profile management and ranking.",
        value ="profile"
        ),
        discord .SelectOption (
        label ="Account Management",
        description ="Commands related to account settings, password, and data deletion.",
        value ="account"
        ),
        discord .SelectOption (
        label ="Premium Commands",
        description ="Exclusive commands for premium users.",
        value ="premium"
        ),
        ]
        super ().__init__ (placeholder ="Select a category to view commands...",min_values =1 ,max_values =1 ,options =options )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("You cannot interact with this dropdown.",ephemeral =True )
            return 

        category =self .values [0 ]
        await show_help_commands (interaction ,category )


        self .disabled =True 
        try :
            if not interaction .response .is_done ():
                await interaction .response .edit_message (view =self .view )
        except discord .errors .InteractionResponded :
            pass 

async def show_help_commands (interaction :discord .Interaction ,category :str ):
    kolkata_tz =timezone ('Asia/Kolkata')
    current_time =datetime .now (kolkata_tz )

    embed =discord .Embed (
    title ="**Lumen Command Help**",
    color =0x000001 ,
    timestamp =current_time 
    )
    embed .set_thumbnail (
    url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=6798af54&is=67975dd4&hm=562bf2cd85caa3c0a401f9b5cb901f1ca6f90565478a3786c4b1c3f1ca946a92&=&format=webp&quality=lossless&width=671&height=671"
    )

    if category =="general":
        embed .description =(
        "**General Commands**\n\n"
        "**+p @user**\n"
        "-# View the profile of a user.\n\n"
        "**+rep @user Your feedback**\n"
        "-# Submit positive feedback for a user.\n\n"
        "**+nrep @user Your feedback**\n"
        "-# Submit negative feedback for a user.\n\n"
        "**+top**\n"
        "-# View the top-ranked users by positive feedback.\n\n"
        "**+hot <daily/weekly/monthly>**\n"
        "-# View the daily/weekly/monthly top-ranked users.\n\n"
        "**+search <keyword1, keyword2>**\n"
        "-# Search profiles using up to 4 keywords.\n\n"
        "**+fbstatus <Feedback ID>**\n"
        "-# Check the status of a specific feedback.\n\n"
        "**+checkserver <server ID>**\n"
        "-# Check if the server is blacklisted or not.\n\n"
        "**+checkwallet <crypto address>**\n"
        "-# Check if the crypto wallet is blacklisted or not.\n\n"
        "**+checkupi <UPI ID/UPI Number>**\n"
        "-# Check if the UPI ID/Number is blacklisted or not.\n\n"
        )
    elif category =="profile":
        embed .description =(
        "**Profile & Ranking Commands**\n\n"
        "**+color <red, green, yellow, blue, white, black>**\n"
        "-# Set your profile color. (Note: Premium users can also set custom colors using hex codes.)\n\n"
        "**+store <details>**\n"
        "-# Update your store details (max 250 characters). Premium users can add a link to their store.\n\n"
        "**+products Product1, Product2, ...**\n"
        "-# Update your product list (Non-premium: up to 3 products; Premium: up to 6 products).\n\n"
        "**+banner <image_url>**\n"
        "-# Set or reset your banner image.\n\n"
        "**+status <status message>**\n"
        "-# Set your profile status. (Non-premium users have limited changes to once per 24 hours; Premium users can change it as many times as they want.)\n"
        )
    elif category =="account":
        embed .description =(
        "**Account Management Commands**\n\n"
        "**+register**\n"
        "-# Register and start using Lumen.\n\n"
        "**+getfeedback <days>**\n"
        "-# Request feedback data in .txt in your DMs.\n\n"
        "**+changepassword or +cpwd**\n"
        "-# Update your password.\n\n"
        "**+requestdatadeletion**\n"
        "-# Request deletion for your data stored with Lumen.\n"
        )
    elif category =="premium":
        embed .description =(
        "**Premium Commands**\n\n"
        "**/premium <redeem-code>**\n"
        "-# Activate Lumen Premium for your account.\n\n"
        "**+getfeedback <all/1-365 days>**\n"
        "-# Request feedback data in both .txt and .pdf formats.\n\n"
        "**+forgotpassword or +cpwd**\n"
        "-# Forgot your password but you must have recovery email setup already.\n\n"
        "**+autofb <1-365days>**\n"
        "-# Automatically send PDF feedback data to your DMs at set intervals.\n\n"
        "**+color <hex code>**\n"
        "-# Set a custom profile color using a hex code.\n\n"
        "**+pfp <url>**\n"
        "-# Set a custom profile picture in your Lumen profile.\n\n"
        "**+storebutton <on/off>**\n"
        "-# Set a custom store link button in your Lumen profile.\n\n"
        "**+button <name>, <url>**\n"
        "-# Set a custom link button in your Lumen profile.\n\n"
        "**+setrecovery**\n"
        "-# Set a recovery email for your Lumen profile (Premium only).\n"
        )

    try :
        if not interaction .response .is_done ():
            await interaction .response .edit_message (embed =embed )
    except discord .errors .InteractionResponded :
        pass 

async def setup (bot ):
    await bot .add_cog (Help (bot ))
