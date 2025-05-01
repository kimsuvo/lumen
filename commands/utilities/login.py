import discord 
from discord .ext import commands 
from discord import Embed 
from discord .ui import Button ,View 
import sqlite3 
import os 

CREDENTIALS_DATABASE_DIR ="credentialsdatabase"




def is_user_registered (user_id ):
    for db_file in os .listdir (CREDENTIALS_DATABASE_DIR ):
        if db_file .endswith (".db"):
            db_path =os .path .join (CREDENTIALS_DATABASE_DIR ,db_file )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(user_id ,))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
    return False 


class SupportServerButton (View ):
    def __init__ (self ):
        super ().__init__ ()
        support_button =Button (label ="Lumen Support Server",url ="https://discord.gg/lumenreport")
        self .add_item (support_button )



class LoginLumen (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (aliases =["recovery","recover"])
    async def login (self ,ctx ):

        if not is_user_registered (ctx .author .id ):
            embed =Embed (
            title ="**Registration Required**",
            description ="<:lumen_dnd:1324983165554524252> You must be registered with Lumen to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed ,delete_after =10 )
            return 


        embed =discord .Embed (
        title ="**Recover your Lumen Profile**",




        color =0x000001 
        )


        embed .add_field (
        name ="**__Steps to Recovery your Lumen Profile__**:",
        value =(
        "-# 1. Join the **[Lumen Support Server](https://discord.gg/lumenreport)**\n"
        "-# 2. Move to <#1328037553680420944> channel.\n"
        "-# 3. Follow the on-screen instructions to complete your profile recovery."
        ),
        inline =False 
        )


        embed .add_field (
        name ="**__Precautions__**:",
        value =(
        "-# 1. Do not share your Lumen email and password with anyone.\n"
        "-# 2. Always verify the authenticity of the server before providing any personal information.\n"
        "-# 3. If you suspect any unauthorized access, contact our support immediately."
        ),
        inline =False 
        )


        embed .add_field (
        name ="**Join Here:**",
        value ="[Click to Join the Lumen Support Server](https://discord.gg/lumenreport)",
        inline =False 
        )


        embed .set_footer (text ="We look forward to your valuable feedback!")


        embed .set_thumbnail (
        url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67771114&is=6775bf94&hm=1a3689e36fdfb8ada96f50548833f6ae089718e582abc1f6fc8344436a3c57d9&=&format=webp&quality=lossless&width=671&height=671"
        )
        view =SupportServerButton ()
        await ctx .send (embed =embed ,view =view )

async def setup (bot ):
    await bot .add_cog (LoginLumen (bot ))