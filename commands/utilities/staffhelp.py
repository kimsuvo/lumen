import discord 
from discord .ext import commands 
from datetime import datetime 
import pytz 
from config import GENERAL_STAFF_ROLE 

class StaffHelpDropdown (discord .ui .Select ):
    def __init__ (self ,user_id ):
        self .user_id =user_id 

        options =[
        discord .SelectOption (label ="Feedback Staff",description ="Commands for managing feedback.",value ="feedback_staff"),
        discord .SelectOption (label ="Report Staff",description ="Commands for reporting and moderation.",value ="report_staff"),
        discord .SelectOption (label ="Management",description ="Commands for server and recovery management.",value ="management"),
        ]

        super ().__init__ (placeholder ="Select a category to view commands...",min_values =1 ,max_values =1 ,options =options )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user .id !=self .user_id :
            await interaction .response .send_message ("This dropdown is only for the user who executed the command.",ephemeral =True )
            return 

        category =self .values [0 ]

        await show_commands (interaction ,category )

async def show_commands (interaction ,category ):
    timezone =pytz .timezone ('Asia/Kolkata')
    embed =discord .Embed (
    title ="Staff Commands",
    description =f"Here are the commands for the **{category .replace ('_',' ').title ()}** category.",
    color =0x000001 ,
    timestamp =datetime .now (timezone )
    )
    embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=6798af54&is=67975dd4&hm=562bf2cd85caa3c0a401f9b5cb901f1ca6f90565478a3786c4b1c3f1ca946a92&=&format=webp&quality=lossless&width=671&height=671")

    if category =="management":
        embed .description =(

        "**+recoverypanel**\n"
        "-# Usage: +recoverypanel\n"
        "-# Sends a recovery profile panel.\n\n"

        "**+viewrecoveries**\n"
        "-# Usage: +viewrecoveries\n"
        "-# Shows the number of pending recovery requests.\n\n"

        "**+confirmrecovery**\n"
        "-# Usage: +confirmrecovery\n"
        "-# Confirms a pending recovery request.\n\n"

        "**+rejectrecovery**\n"
        "-# Usage: +rejectrecovery\n"
        "-# Rejects a pending recovery request.\n\n"

        "**+pendingfeedbackall <all/premium/normal>**\n"
        "-# Usage: +pendingverificationfball\n"
        "-# Sends the pending feedbacks of Lumen.\n\n"

        "**+pendingverificationfball <all/premium/normal>**\n"
        "-# Usage: +pendingverificationfball\n"
        "-# Sends the pending verification feedbacks of Lumen.\n"

        )

    elif category =="feedback_staff":
        embed .description =(
        "**+view**\n"
        "-# Usage: +view [user]\n"
        "-# Displays pending feedback for the specified user, or your own if no user is provided.\n\n"

        "**+confirmpending (alias: +cp)**\n"
        "-# Usage: +confirmpending <feedback ID>\n"
        "-# Confirm a pending feedback with the given vouch number.\n\n"

        "**+rejectpending (alias: +rp)**\n"
        "-# Usage: +rejectpending <feedback ID> [reason]\n"
        "-# Reject a pending feedback with an optional reason.\n\n"

        "**+verifyfeedback (alias: +vf)**\n"
        "-# Usage: +verifyfeedback <feedback ID>\n"
        "-# Verify a feedback submission using its vouch number.\n\n"

        "**+pfvall**\n"
        "-# Usage: +pfvall\n"
        "-# View all pending feedbacks in verification.\n\n"

        "**+pall**\n"
        "-# Usage: +pall\n"
        "-# View all pending feedbacks.\n"
        )

    elif category =="report_staff":
        embed .description =(
        "**+dwc**\n"
        "-# Usage: +dwc <user_id or mention or username>\n"
        "-# Toggle the Do Not Work tag for a user.\n\n"

        "**+blacklist**\n"
        "-# Usage: +blacklist <user> <reason>\n"
        "-# Blacklist a user from receiving feedback.\n\n"

        "**+unblacklist**\n"
        "-# Usage: +unblacklist <user>\n"
        "-# Removes a blacklist from a user.\n\n"

        "**+warn**\n"
        "-# Usage: +warn <user> <reason>\n"
        "-# Issues a warning to the user.\n\n"

        "**+warnlist**\n"
        "-# Usage: +warnlist <user>\n"
        "-# Displays the user’s existing warnings.\n\n"

        "**+warnremove**\n"
        "-# Usage: +warnremove <warn ID>\n"
        "-# Removes a specific warning from the user.\n\n"

        "**+checkblacklist**\n"
        "-# Usage: +checkblacklist <user>\n"
        "-# Checks if the user is blacklisted.\n\n"

        "**+colormode**\n"
        "-# Usage: +colormode <user>\n"
        "-# Changes the color mode of a user.\n\n"

        "**+lockcolor**\n"
        "-# Usage: +lockcolor <user> <red/yellow/black>\n"
        "-# Sets a color for a user's profile.\n\n"

        "**+lockstatus**\n"
        "-# Usage: +lockstatus <user> <status>\n"
        "-# Locks the specified user’s status.\n\n"

        "**+statusmode**\n"
        "-# Usage: +statusmode <user>\n"
        "-# Changes the status mode of a user.\n\n"

        "**+blserver**\n"
        "-# Usage: +blserver <server ID> <reason>\n"
        "-# Blacklists a server.\n\n"

        "**+unblserver**\n"
        "-# Usage: +unblserver <server ID>\n"
        "-# Unblacklists a server.\n\n"

        "**+conp**\n"
        "-# Usage: +conp <Feedback ID>\n"
        "-# Confirms a pending Feedback ID.\n\n"

        "**+rejectp**\n"
        "-# Usage: +rejectp <Feedback ID>\n"
        "-# Rejects a pending Feedback ID.\n\n"

        "**+verifyfb**\n"
        "-# Usage: +conp <Feedback ID>\n"
        "-# Sends a pending Feedback ID for verification.\n\n"

        "**+penall**\n"
        "-# Usage: +penall <batch numner> (1 for Normal Batches, p1 for Premium Batches)\n"
        "-# See pending feedbacks for specified batch.\n\n"

        "**+penfvall**\n"
        "-# Usage: +penfvall <batch numner> (1 for Normal Batches, p1 for Premium Batches)\n"
        "-# See pending verification feedbacks for specified batch.\n\n"

        )


    await interaction .response .edit_message (embed =embed )

class StaffHelp (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="staffhelp")
    async def staff_help (self ,ctx ):

        if not any (role .id in GENERAL_STAFF_ROLE for role in ctx .author .roles ):
            timezone =pytz .timezone ('Asia/Kolkata')
            embed =discord .Embed (
            title ="**__Permission Denied__**",
            description ="You do not have permission to use the staff help command.\n-# Contact your server admin if you believe this is an error.",
            color =0xff0000 ,
            timestamp =datetime .now (timezone )
            )
            await ctx .send (embed =embed )
            return 

        timezone =pytz .timezone ('Asia/Kolkata')
        embed =discord .Embed (
        title ="**__Staff Commands Help__**",
        description =(
        "**Welcome, Staff Member!**\n\n"
        "**__Feedback Staff__**\n"
        "-# Commands to view, confirm, reject, or verify pending feedback.\n\n"
        "**__Report Staff__**\n"
        "-# Commands to manage reports, warnings, and blacklists.\n\n"
        "**__Management__**\n"
        "-# Commands for adding/removing servers, listing allowed servers, and managing recoveries.\n\n"
        ),
        color =0x000001 ,
        timestamp =datetime .now (timezone )
        )

        embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png")

        view =discord .ui .View ()
        view .add_item (StaffHelpDropdown (ctx .author .id ))


        await ctx .send (embed =embed ,view =view )

async def setup (bot ):
    await bot .add_cog (StaffHelp (bot ))
