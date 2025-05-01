
import os 
import sqlite3 
import discord 
from discord .ext import commands 
import config 
from functions .color_functions import db_utils 

class ColorMode (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .database_dir =db_utils .DATABASE_DIR 
        if not os .path .exists (self .database_dir ):
            os .makedirs (self .database_dir )

    @commands .command (name ="colormode")
    @commands .check (lambda ctx :any (role .id in config .REPORT_STAFF_ROLE for role in ctx .author .roles ))
    async def colormode (self ,ctx ,member :discord .Member ):
        user_id =str (member .id )
        db_file =db_utils .find_user_db (user_id )

        if db_file is None :
            error_embed =discord .Embed (
            title ="Error",
            description =f"{member .mention } does not have a color set yet.",
            color =0xff0000 
            )
            await ctx .send (embed =error_embed )
            return 


        conn =sqlite3 .connect (db_file )
        c =conn .cursor ()
        c .execute ("SELECT colorlock FROM colors WHERE user_id=?",(user_id ,))
        result =c .fetchone ()
        if result is None :
            error_embed =discord .Embed (
            title ="Error",
            description ="Unexpected error: could not retrieve the user's data.",
            color =0xff0000 
            )
            await ctx .send (embed =error_embed )
            conn .close ()
            return 

        current_lock =result [0 ]
        new_lock ="no"if current_lock =="yes"else "yes"

        c .execute ("UPDATE colors SET colorlock=? WHERE user_id=?",(new_lock ,user_id ))
        conn .commit ()
        conn .close ()

        success_embed =discord .Embed (
        title ="Success",
        description =f"{member .mention }'s color lock has been set to **{new_lock }**.",
        color =0x000001 
        )
        await ctx .send (embed =success_embed )

async def setup (bot ):
    await bot .add_cog (ColorMode (bot ))
