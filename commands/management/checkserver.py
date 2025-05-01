import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 
import sqlite3 
import os 
import glob 

class CheckServerCog (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .db_dir ='serverblacklistdatabase'

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command (name ="checkserver")
    async def checkserver (self ,ctx ,server_id :str ):
        """Checks if a server is blacklisted across all databases."""
        blacklisted =False 


        db_files =glob .glob (os .path .join (self .db_dir ,'*.db'))

        for db_file in db_files :

            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT * FROM server_blacklist WHERE server_id = ?",(server_id ,))
            row =cursor .fetchone ()
            conn .close ()

            if row :
                blacklisted =True 
                break 

        if blacklisted :
            embed =discord .Embed (
            title ="Server Blacklisted",
            description =f"Server ID {server_id } is currently blacklisted.",
            color =discord .Color .red ()
            )
        else :
            embed =discord .Embed (
            title ="Server Not Blacklisted",
            description =f"Server ID {server_id } is not blacklisted.",
            color =discord .Color .green ()
            )

        await ctx .send (embed =embed )

    @checkserver .error 
    async def profile_prefix_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):

            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =(f"You're on cooldown! Please try again in **{error .retry_after :.1f} seconds**."),
            color =0xff0000 ,
            timestamp =discord .utils .utcnow ()
            )
            cooldown_embed .set_footer (
            text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :
            raise error 

async def setup (bot ):
    await bot .add_cog (CheckServerCog (bot ))
