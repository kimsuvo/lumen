import discord 
from discord .ext import commands 
import sqlite3 
import os 
import re 
from config import MANAGEMENT_ROLE_ID 

class VerifiedTickBadge (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .db_dir ="verifiedusers"

        if not os .path .exists (self .db_dir ):
            os .makedirs (self .db_dir )

    @commands .command (name ="vb")
    async def verifiedbadge (self ,ctx ,member :discord .Member ,tick_type :str ):

        management_ids =MANAGEMENT_ROLE_ID if isinstance (MANAGEMENT_ROLE_ID ,(list ,tuple ))else [MANAGEMENT_ROLE_ID ]


        if not any (role .id in management_ids for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="Error",
            description ="You do not have permission to use this command.",
            color =0xff0000 
            )
            return await ctx .send (embed =embed )


        tick_type =tick_type .lower ()
        tick_names ={
        "staff":"<:staff_verified:1341794457896489000>",
        "premium":"<:premium_verified:1341794427378864208>",
        "svprem":"<:premium_server_owner:1341794430751080540>",
        "partner":"<:lumen_partner_verified:1341794424652431380>",
        "lumen":"<:lumen_verified:1341794361930940456>"
        }
        if tick_type not in tick_names :
            embed =discord .Embed (
            title ="Error",
            description ="Invalid tick type provided. Valid types: staff, premium, svprem, partner, lumen.",
            color =0xff0000 
            )
            return await ctx .send (embed =embed )

        tick_emoji =tick_names [tick_type ]
        user_id =str (member .id )


        db_files =[]
        for filename in os .listdir (self .db_dir ):
            match =re .match (r"verified_(\d+)\.db",filename )
            if match :
                number =int (match .group (1 ))
                db_files .append ((number ,filename ))

        db_files .sort (key =lambda x :x [0 ])


        if not db_files :
            db_index =1 
            db_file =f"verified_{db_index }.db"
            db_path =os .path .join (self .db_dir ,db_file )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
            conn .commit ()
            conn .close ()
            db_files .append ((db_index ,db_file ))


        updated =False 
        for number ,filename in db_files :
            db_path =os .path .join (self .db_dir ,filename )
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()

            c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
            conn .commit ()

            c .execute ("SELECT * FROM verified WHERE user_id = ?",(user_id ,))
            if c .fetchone ():

                c .execute ("UPDATE verified SET tick_name = ? WHERE user_id = ?",(tick_emoji ,user_id ))
                conn .commit ()
                conn .close ()
                updated =True 
                embed =discord .Embed (
                title ="Success",
                description =f"Updated tick for {member .mention } to {tick_emoji }",
                color =0x000001 
                )
                await ctx .send (embed =embed )
                break 
            conn .close ()

        if not updated :

            inserted =False 
            for number ,filename in db_files :
                db_path =os .path .join (self .db_dir ,filename )
                conn =sqlite3 .connect (db_path )
                c =conn .cursor ()
                c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
                conn .commit ()

                c .execute ("SELECT COUNT(*) FROM verified")
                count =c .fetchone ()[0 ]
                if count <20000 :
                    c .execute ("INSERT INTO verified (user_id, tick_name) VALUES (?, ?)",(user_id ,tick_emoji ))
                    conn .commit ()
                    conn .close ()
                    inserted =True 
                    embed =discord .Embed (
                    title ="Success",
                    description =f"Added tick for {member .mention } as {tick_emoji }",
                    color =0x000001 
                    )
                    await ctx .send (embed =embed )
                    break 
                conn .close ()


            if not inserted :
                new_index =db_files [-1 ][0 ]+1 
                db_file =f"verified_{new_index }.db"
                db_path =os .path .join (self .db_dir ,db_file )
                conn =sqlite3 .connect (db_path )
                c =conn .cursor ()
                c .execute ("CREATE TABLE IF NOT EXISTS verified (user_id TEXT PRIMARY KEY, tick_name TEXT)")
                conn .commit ()
                c .execute ("INSERT INTO verified (user_id, tick_name) VALUES (?, ?)",(user_id ,tick_emoji ))
                conn .commit ()
                conn .close ()
                embed =discord .Embed (
                title ="Success",
                description =f"Database full. Created new database and added tick for {member .mention } as {tick_emoji }.",
                color =0x000001 
                )
                await ctx .send (embed =embed )

async def setup (bot ):
    await bot .add_cog (VerifiedTickBadge (bot ))
