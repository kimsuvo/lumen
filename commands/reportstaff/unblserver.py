import discord 
from discord .ext import commands 
import sqlite3 
import os 

from discord import SyncWebhook 


from datetime import datetime 
import pytz 


from config import REPORT_STAFF_ROLE ,BLACKLIST_CHANNEL_ID 


IST =pytz .timezone ("Asia/Kolkata")

class UnBLServerCog (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .database_directory ='serverblacklistdatabase'
        if not os .path .exists (self .database_directory ):
            raise FileNotFoundError (f"Directory not found: {self .database_directory }")

    @commands .command (name ="unblserver")
    @commands .has_any_role (*REPORT_STAFF_ROLE )
    async def unblserver (self ,ctx ,server_id :str ):
        """
        Removes a server by ID from the blacklist database, sends a webhook notification,
        and posts a confirmation embed in the current channel.
        """

        now_ist =datetime .now (IST )
        timestamp_ist_str =now_ist .strftime ("%Y-%m-%d %H:%M:%S IST")

        found =False 

        for file in os .listdir (self .database_directory ):
            if file .endswith ('.db'):
                db_path =os .path .join (self .database_directory ,file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT * FROM server_blacklist WHERE server_id = ?",(server_id ,))
                row =cursor .fetchone ()
                if row :
                    cursor .execute ("DELETE FROM server_blacklist WHERE server_id = ?",(server_id ,))
                    conn .commit ()
                    found =True 
                conn .close ()

        if found :

            webhook_embed =discord .Embed (
            title ="Server Unblacklisted",
            color =discord .Color .green (),
            timestamp =datetime .now (IST )
            )

            server =self .bot .get_guild (int (server_id ))
            webhook_embed .add_field (name ="Server ID",value =server_id ,inline =False )
            webhook_embed .add_field (
            name ="Unblacklisted By",
            value =f"{ctx .author } (ID: {ctx .author .id })",
            inline =False 
            )
            webhook_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )

            if server and server .icon :
                webhook_embed .set_thumbnail (url =server .icon .url )

            webhook_embed .set_image (
            url ="https://media.discordapp.net/attachments/1200750312844165203/1333069505223721045/serverunblacklisted.png?ex=67978d39&is=67963bb9&hm=611885615de8b6e6a1b4f7d27a02d26f1d7fddd4d291ad0c274f00c93b76f5c2&=&format=webp&quality=lossless"
            )

            blacklist_channel =self .bot .get_channel (BLACKLIST_CHANNEL_ID )
            if blacklist_channel :
                await blacklist_channel .send (embed =webhook_embed )


            confirmation_embed =discord .Embed (
            title ="Server Unblacklist Confirmation",
            description =f"Server with ID `{server_id }` has been **unblacklisted** successfully.",
            color =discord .Color .green (),
            timestamp =now_ist 
            )
            confirmation_embed .add_field (name ="Unblacklisted By",value =ctx .author .mention ,inline =False )
            confirmation_embed .add_field (name ="Timestamp (IST)",value =timestamp_ist_str ,inline =False )

            await ctx .send (embed =confirmation_embed )
        else :
            not_found_embed =discord .Embed (
            title ="Server Not Found",
            description =f"No blacklisted server found with ID `{server_id }`.",
            color =discord .Color .orange ()
            )
            await ctx .send (embed =not_found_embed )

async def setup (bot ):
    await bot .add_cog (UnBLServerCog (bot ))
