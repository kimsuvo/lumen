import discord 
from discord .ext import commands 
import os 
import time 
import psutil 
import platform 
from config import BOT_INFO_PASSWORD ,DEV_CHAMBER_ROLE 
from discord .ui import Button ,View 
import asyncio 

password =BOT_INFO_PASSWORD 


def get_cpu_temperature ():
    try :

        if platform .system ()=="Linux":
            if hasattr (psutil ,"sensors_temperatures"):
                temps =psutil .sensors_temperatures ()
                if "coretemp"in temps :
                    cpu_temp =temps ["coretemp"][0 ].current 
                    return f"{cpu_temp :.2f} °C"
                return "coretemp sensor not found"
        elif platform .system ()=="Windows":

            return "Not available (Windows)"
        elif platform .system ()=="Darwin":

            return "Not available (macOS)"
        else :
            return "Not available (unknown platform)"
    except Exception as e :
        return f"Error: {str (e )}"



def get_cpu_speed ():
    try :
        cpu_freq =psutil .cpu_freq ()
        return f"{cpu_freq .current :.2f} MHz"
    except Exception as e :
        return f"Error: {str (e )}"


def get_ram_speed ():
    return "N/A (requires additional tools)"

class PasswordModal (discord .ui .Modal ):
    def __init__ (self ):
        super ().__init__ (title ="Password Entry")
        self .password_input =discord .ui .TextInput (
        label ="Password",
        style =discord .TextStyle .short ,
        placeholder ="Enter the password",
        required =True ,
        )
        self .add_item (self .password_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        if self .password_input .value ==password :
            embed =create_botinfo_embed (interaction .client )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        else :
            await interaction .response .send_message ("Incorrect password.",ephemeral =True )

class BotInfoView (View ):
    def __init__ (self ):
        super ().__init__ ()

    @discord .ui .button (label ="ENTER PASSWORD",style =discord .ButtonStyle .success )
    async def enter_password (self ,interaction :discord .Interaction ,button :Button ):
        await interaction .response .send_modal (PasswordModal ())

    @discord .ui .button (label ="CANCEL",style =discord .ButtonStyle .red )
    async def cancel (self ,interaction :discord .Interaction ,button :Button ):
        await interaction .message .delete ()


def create_botinfo_embed (bot ):
    process =psutil .Process (os .getpid ())
    cpu_usage =psutil .cpu_percent (interval =1 )
    memory_info =process .memory_info ()
    ram_usage =memory_info .rss /(1024 **2 )
    total_ram =psutil .virtual_memory ().total /(1024 **3 )
    disk_usage =psutil .disk_usage ('/')
    number_of_servers =len (bot .guilds )

    embed =discord .Embed (
    title ="**Lumen System Information**",
    description ="Here is the detailed status of the bot and its system:",
    color =discord .Color .from_str ("#ffb03b")
    )
    embed .add_field (name ="Developer",value ="Gaurav",inline =False )
    embed .add_field (name ="Language",value ="Python",inline =False )
    embed .add_field (name ="Bot Ping",value =f"```{round (bot .latency *1000 )}ms```",inline =True )
    embed .add_field (name ="CPU Usage",value =f"```{cpu_usage }%```",inline =True )
    embed .add_field (name ="RAM Usage",value =f"```{ram_usage :.2f} MB```",inline =True )
    embed .add_field (name ="Total RAM",value =f"```{total_ram :.2f} GB```",inline =True )
    embed .add_field (name ="Disk Usage",value =f"```{disk_usage .percent }% used ({disk_usage .used //(1024 **3 )} GB of {disk_usage .total //(1024 **3 )} GB)```",inline =False )
    embed .add_field (name ="Response Time",value =f"```{round (bot .latency *1000 )} ms```",inline =True )
    embed .add_field (name ="Number of Servers",value =f"```{number_of_servers }```",inline =True )
    embed .add_field (name ="CPU Speed",value =f"```{get_cpu_speed ()}```",inline =True )
    embed .add_field (name ="CPU Temperature",value =f"```{get_cpu_temperature ()}```",inline =True )
    return embed 

class BotInfo (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command ()
    async def botinfo (self ,ctx ):
        if not any (role .id ==DEV_CHAMBER_ROLE for role in ctx .author .roles ):
            error_embed =discord .Embed (
            title ="Permission Denied",
            description ="You do not have the required permissions to run this command.",
            color =0xff0000 
            )
            await ctx .send (embed =error_embed ,delete_after =5 )
            await ctx .message .delete ()
            return 

        embed =discord .Embed (
        title ="**Lumen Information (Admin Only)**",
        description ="Please click 'Enter Password' to proceed.",
        color =0xffb03b 
        )
        view =BotInfoView ()
        await ctx .send (embed =embed ,view =view )
        await ctx .message .delete ()

async def setup (bot ):
    await bot .add_cog (BotInfo (bot ))