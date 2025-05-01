

import discord 
from discord .ext import commands 
import sqlite3 
import os 
import re 

from config import GUILD_ID ,USER_WHITELIST_CATEGORIES 

class ServerInviteListener (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

        self .DB_DIRECTORY ="serverblacklistdatabase"
        self .DB_PREFIX ="server_"
        self .DB_EXTENSION =".db"

    @commands .Cog .listener ()
    async def on_message (self ,message :discord .Message ):

        if message .guild is None or message .guild .id !=GUILD_ID or message .author .bot :
            return 


        if message .channel .category and message .channel .category .id in USER_WHITELIST_CATEGORIES :
            return 


        invite_pattern =r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.com/invite|discord\.gg)/([a-zA-Z0-9-]+)"
        invite_codes =re .findall (invite_pattern ,message .content )
        if not invite_codes :
            return 

        for code in invite_codes :
            try :

                invite =await self .bot .fetch_invite (code )
            except Exception :

                continue 


            if invite .guild is None :
                continue 


            server_id =str (invite .guild .id )
            found_server =None 


            if os .path .exists (self .DB_DIRECTORY ):
                for filename in os .listdir (self .DB_DIRECTORY ):
                    if filename .startswith (self .DB_PREFIX )and filename .endswith (self .DB_EXTENSION ):
                        db_path =os .path .join (self .DB_DIRECTORY ,filename )
                        try :
                            conn =sqlite3 .connect (db_path )
                            cursor =conn .cursor ()
                            cursor .execute ("SELECT server_id FROM server_blacklist")
                            rows =cursor .fetchall ()
                            conn .close ()


                            for row in rows :
                                if row [0 ]==server_id :
                                    found_server =server_id 
                                    break 
                            if found_server :
                                break 
                        except sqlite3 .Error :
                            continue 


            if found_server :
                try :
                    await message .delete ()
                except discord .Forbidden :
                    pass 

                warning_embed =discord .Embed (
                title ="**Warning**",
                description =f"**Blacklisted Server detected**:\n{found_server }.",
                color =0xff0000 
                )
                warning_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1327174872908042270/blacklisted_logo_thumb.png?ex=67bf692b&is=67be17ab&hm=ca92ef881b23f24756826735fad3eb0c5679f870f3afd0fa3086ce8371f726db&=&format=webp&quality=lossless&width=671&height=671")
                await message .channel .send (embed =warning_embed ,delete_after =5 )


                break 

async def setup (bot :commands .Bot ):
    await bot .add_cog (ServerInviteListener (bot ))
