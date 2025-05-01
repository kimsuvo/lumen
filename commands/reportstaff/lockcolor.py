
import os 
import sqlite3 
import discord 
from discord .ext import commands 
import config 
from functions .color_functions import db_utils 

class LockColor (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

        self .database_dir =db_utils .DATABASE_DIR 
        if not os .path .exists (self .database_dir ):
            os .makedirs (self .database_dir )

    @commands .command (name ="lockcolor")
    @commands .has_any_role (*config .REPORT_STAFF_ROLE )
    async def lockcolor (self ,ctx ,member :discord .Member ,color_option :str ):
        color_map ={
        "red":"#ff0000",
        "yellow":"#fbb03b",
        "black":"#000001"
        }
        option =color_option .lower ()
        if option not in color_map :
            error_embed =discord .Embed (
            title ="Error",
            description ="Invalid color option! Please choose from `red`, `yellow`, or `black`.",
            color =0xff0000 
            )
            await ctx .send (embed =error_embed )
            return 

        hex_color =color_map [option ]
        user_id =str (member .id )
        db_file =db_utils .find_user_db (user_id )

        if db_file :
            conn =sqlite3 .connect (db_file )
            c =conn .cursor ()
            c .execute ("UPDATE colors SET color=?, colorlock=? WHERE user_id=?",(hex_color ,"yes",user_id ))
            conn .commit ()
            conn .close ()
        else :
            active_db =db_utils .get_active_db ()
            conn =sqlite3 .connect (active_db )
            c =conn .cursor ()
            c .execute ("INSERT INTO colors (user_id, color, colorlock) VALUES (?, ?, ?)",(user_id ,hex_color ,"yes"))
            conn .commit ()
            conn .close ()

        success_embed =discord .Embed (
        title ="Success",
        description =f"{member .mention }'s color has been set to **{hex_color }** and locked.",
        color =0x000001 
        )
        await ctx .send (embed =success_embed )

async def setup (bot ):
    await bot .add_cog (LockColor (bot ))
