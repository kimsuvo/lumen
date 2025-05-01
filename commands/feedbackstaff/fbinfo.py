

import discord 
import sqlite3 
import os 
from discord .ext import commands 
from config import FEEDBACK_ADMIN_ROLE 

class FBInfo (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .check (lambda ctx :any (role .id in FEEDBACK_ADMIN_ROLE for role in ctx .author .roles ))
    @commands .command (aliases =["fi"])
    async def fbinfo (self ,ctx ,member :str =None ):
        """
        Displays the number of confirmations, rejections, and verifications an admin has performed.
        Usage:
        - +fbinfo or +fi : Shows your own counts.
        - +fbinfo @User or +fi @User : Shows the counts for the mentioned user.
        - +fbinfo all or +fi all : Shows the total counts for all users from all databases.
        """

        if member and member .lower ()=="all":
            total_confirm =total_reject =total_verify =0 
            database_directory ="infodatabase"

            for filename in os .listdir (database_directory ):
                if filename .endswith (".db"):
                    db_path =os .path .join (database_directory ,filename )
                    try :
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()
                        cursor .execute ("""
                            SELECT 
                                SUM(confirm_count),
                                SUM(reject_count),
                                SUM(verify_count)
                            FROM cpinfo
                        """)
                        result =cursor .fetchone ()
                        conn .close ()

                        if result :

                            c ,r ,v =result 
                            total_confirm +=c if c is not None else 0 
                            total_reject +=r if r is not None else 0 
                            total_verify +=v if v is not None else 0 
                    except sqlite3 .Error as e :

                        print (f"Error reading {db_path }: {e }")
                        continue 

            embed =discord .Embed (
            title ="**Feedback Staff Information (Lumen Staff Chamber)**",
            description ="Here are the total feedback actions processed.",
            color =0x000001 ,
            timestamp =discord .utils .utcnow ()
            )
            embed .add_field (name ="Confirmations",value =f"**{total_confirm }**",inline =True )
            embed .add_field (name ="Rejections",value =f"**{total_reject }**",inline =True )
            embed .add_field (name ="Verifications",value =f"**{total_verify }**",inline =True )
            embed .set_footer (text ="Powered by Lumen")

            await ctx .send (embed =embed )
            return 


        if member is None :
            member_obj =ctx .author 
        else :

            try :
                member_obj =await commands .MemberConverter ().convert (ctx ,member )
            except commands .BadArgument :
                embed =discord .Embed (
                title ="**Invalid Member**",
                description ="Please mention a valid member to view their feedbacks info.",
                color =0xFF0000 
                )
                await ctx .send (embed =embed )
                return 


        try :
            conn =sqlite3 .connect ('infodatabase/cpinfo.db')
            cursor =conn .cursor ()
        except sqlite3 .Error as e :
            embed =discord .Embed (
            title ="**Database Error**",
            description =f"An error occurred while connecting to the database: {e }",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )
            return 


        try :
            cursor .execute ("""
                SELECT confirm_count, reject_count, verify_count 
                FROM cpinfo 
                WHERE user_id = ?
            """,(str (member_obj .id ),))
            result =cursor .fetchone ()
            if result :
                confirm_count ,reject_count ,verify_count =result 
            else :
                confirm_count =reject_count =verify_count =0 
        except sqlite3 .Error as e :
            embed =discord .Embed (
            title ="**Database Error**",
            description =f"An error occurred while fetching data: {e }",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )
            conn .close ()
            return 

        conn .close ()


        embed =discord .Embed (
        title ="**Feedback Staff Information**",
        description =f"Here are the feedback action counts for {member_obj .mention }.",
        color =0x000001 ,
        timestamp =discord .utils .utcnow ()
        )
        embed .add_field (name ="Confirmations",value =f"**{confirm_count }**",inline =True )
        embed .add_field (name ="Rejections",value =f"**{reject_count }**",inline =True )
        embed .add_field (name ="Verifications",value =f"**{verify_count }**",inline =True )
        embed .set_thumbnail (url =member_obj .avatar .url if member_obj .avatar else member_obj .default_avatar .url )
        embed .set_footer (text ="Powered by Lumen")

        await ctx .send (embed =embed )

    @fbinfo .error 
    async def fbinfo_error (self ,ctx ,error ):
        if isinstance (error ,commands .MissingRole ):
            embed =discord .Embed (
            title ="**Access Denied**",
            description ="You do not have the required role to use this command.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )
        elif isinstance (error ,commands .BadArgument ):
            embed =discord .Embed (
            title ="**Invalid Member**",
            description ="Please mention a valid member to view their confirmation info.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )
        else :
            embed =discord .Embed (
            title ="**Error**",
            description ="An unexpected error occurred.",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )


async def setup (bot ):
    await bot .add_cog (FBInfo (bot ))
