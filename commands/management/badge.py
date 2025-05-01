import sqlite3 
import discord 
from discord .ext import commands 
from config import BADGE_PERMISSIONS 
import os 
import logging 


DATABASE_DIR ={
'credentials':"credentialsdatabase",
'badges':"badgesdatabase"
}



os .makedirs (DATABASE_DIR ['credentials'],exist_ok =True )
os .makedirs (DATABASE_DIR ['badges'],exist_ok =True )

class BadgeManagement (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 



    logging .basicConfig (
    filename ='bot_errors.log',
    level =logging .ERROR ,
    format ='%(asctime)s:%(levelname)s:%(message)s'
    )

    def load_credentials (self ):
        credentials_list =[]
        credentials_dir =DATABASE_DIR ['credentials']


        if not os .path .exists (credentials_dir ):
            logging .error (f"Credentials directory '{credentials_dir }' does not exist.")
            return credentials_list 


        for db_file in os .listdir (credentials_dir ):
            if db_file .endswith ('.db'):
                db_path =os .path .join (credentials_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()


                    cursor .execute ('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL,
                            password TEXT NOT NULL,
                            recovery_email TEXT,
                            created_by TEXT,
                            created_at TEXT,
                            key TEXT UNIQUE NOT NULL
                        )
                    ''')
                    conn .commit ()


                    cursor .execute ('SELECT * FROM users')
                    credentials =cursor .fetchall ()


                    for credential in credentials :
                        credentials_list .append ({
                        'user_id':credential [0 ],
                        'username':credential [1 ],
                        'password':credential [2 ],
                        'recovery_email':credential [3 ],
                        'created_by':credential [4 ],
                        'created_at':credential [5 ],
                        'key':credential [6 ]
                        })
                except sqlite3 .OperationalError as e :
                    logging .error (f"OperationalError in '{db_file }': {e }")

                except sqlite3 .Error as e :
                    logging .error (f"SQLite error in '{db_file }': {e }")

                finally :
                    conn .close ()

        return credentials_list 


    def get_badges_db_path (self ,user_id =None ):
        badges_dir =DATABASE_DIR ['badges']
        os .makedirs (badges_dir ,exist_ok =True )


        existing_dbs =sorted ([
        f for f in os .listdir (badges_dir )
        if f .startswith ('badges_')and f .endswith ('.db')and f .split ('_')[1 ].split ('.')[0 ].isdigit ()
        ],key =lambda x :int (x .split ('_')[1 ].split ('.')[0 ]))

        if not existing_dbs :
            return os .path .join (badges_dir ,'badges_1.db')


        if user_id :
            for db_file in existing_dbs :
                db_path =os .path .join (badges_dir ,db_file )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ('SELECT user_id FROM badges WHERE user_id = ?',(user_id ,))
                if cursor .fetchone ():
                    conn .close ()
                    return db_path 
                conn .close ()


        last_db =existing_dbs [-1 ]
        conn =sqlite3 .connect (os .path .join (badges_dir ,last_db ))
        cursor =conn .cursor ()
        cursor .execute ('''
            CREATE TABLE IF NOT EXISTS badges (
                user_id TEXT PRIMARY KEY,
                badge_count TEXT
            )
        ''')

        cursor .execute ('SELECT COUNT(*) FROM badges')
        count =cursor .fetchone ()[0 ]
        conn .close ()

        if count >=15000 :
            new_db_number =int (last_db .split ('_')[1 ].split ('.')[0 ])+1 
            return os .path .join (badges_dir ,f'badges_{new_db_number }.db')
        else :
            return os .path .join (badges_dir ,last_db )

    def load_badges (self ):
        badges_list =[]
        badges_dir =DATABASE_DIR ['badges']


        for db_file in os .listdir (badges_dir ):
            if db_file .endswith ('.db')and db_file .startswith ('badges_'):
                conn =sqlite3 .connect (os .path .join (badges_dir ,db_file ))
                cursor =conn .cursor ()

                cursor .execute ('''
                    CREATE TABLE IF NOT EXISTS badges (
                        user_id TEXT PRIMARY KEY,
                        badge_count TEXT
                    )
                ''')

                cursor .execute ('SELECT * FROM badges')
                badges =cursor .fetchall ()

                conn .close ()

                for badge in badges :
                    badges_list .append ({
                    'user_id':badge [0 ],
                    'badge_count':badge [1 ]
                    })

        return badges_list 


    def save_badges (self ,badges ):
        for badge in badges :
            user_id =badge ['user_id']
            db_path =self .get_badges_db_path (user_id )
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()


            cursor .execute ('''
                CREATE TABLE IF NOT EXISTS badges (
                    user_id TEXT PRIMARY KEY,
                    badge_count TEXT
                )
            ''')


            cursor .execute (''' 
                INSERT OR REPLACE INTO badges (user_id, badge_count)
                VALUES (?, ?)
            ''',(user_id ,badge ['badge_count']))

            conn .commit ()
            conn .close ()


    async def send_congrats_dm (self ,user ,badge_emojis ):
        try :
            dm =await user .create_dm ()
            embed =discord .Embed (
            title ="**Congratulations!**",
            description =f"You have received the following badges: {badge_emojis }",
            color =0x000001 
            )
            await dm .send (embed =embed )
        except Exception as e :
            print (f"Error sending DM to {user .display_name }: {str (e )}")


    @commands .command (name ="badge")
    async def badge (self ,ctx ,user :discord .User ,*badge_counts :str ):

        def error_embed (message ):
            embed =discord .Embed (description =message ,color =0xFF0000 )
            return embed 


        def success_embed (message ):
            embed =discord .Embed (description =message ,color =0x000001 )
            return embed 


        if not any (role .id in BADGE_PERMISSIONS for role in ctx .author .roles ):
            embed =error_embed ("You do not have the required role to use this command.")
            await ctx .send (embed =embed )
            return 


        try :

            badge_emojis ={
            "premium":"<:lumen_premium_badge:1335561446284857445>",
            "staff":"<:lumen_staff:1324762451845054504>",
            "developer":"<:lumen_developer:1329352036407316521>",
            "supporter":"<:lumen_support:1329355079563743282>",
            "booster":"<:lumen_booster:1324759084238508083>",
            "partner":"<:lumen_partner:1324759142828736523>",
            "top":"<:lumen_top:1324758834820026378>",


            "50":"<:lumen_50:1324758839857516564>",
            "100":"<:lumen_100:1324758869800390656>",
            "150":"<:lumen_150:1324758863672508466>",
            "200":"<:lumen_200:1324758852272652371>",
            "250":"<:lumen_250:1324758858614312990>",
            "300":"<:lumen_300:1324758845091872852>",
            "375":"<:lumen_375:1324758837047332864>",
            "450":"<:lumen_450:1324758872300327045>",
            "525":"<:lumen_525:1324758866063396864>",
            "750":"<:lumen_750:1324758847054938244>",
            "1000":"<:lumen_1000:1324758829891715193>",
            "1250":"<:lumen_1250:1324758832563617792>",
            "1600":"<:lumen_1600:1324758855581696020>",
            "2000":"<:lumen_2000:1324758849823182919>",
            "3000":"<:lumen_3000:1324758842235686933>"
            }



            badge_order_roles =[
            "premium",
            "staff",
            "developer",
            "supporter",
            "booster",
            "partner",
            "top"
            ]
            badge_order_numerics =[
            "50","100","150","200","250","300","375",
            "450","525","750","1000","1250","1600","2000","3000"
            ]

            badge_order =badge_order_roles +badge_order_numerics 


            credentials =self .load_credentials ()
            user_data =next ((u for u in credentials if str (u ['user_id'])==str (user .id )),None )

            if not user_data :
                embed =error_embed (f"The user {user .display_name } is not registered.")
                await ctx .send (embed =embed )
                return 


            badges =self .load_badges ()
            user_badge =next ((b for b in badges if str (b ['user_id'])==str (user .id )),None )


            if not badge_counts :
                if user_badge :
                    user_badge ['badge_count']=""
                    self .save_badges (badges )
                await ctx .send (embed =success_embed ("All badges removed."))
                return 


            input_keys =set (badge_counts )
            valid_input_keys =[key for key in input_keys if key in badge_emojis ]

            if not valid_input_keys :
                await ctx .send (embed =error_embed ("No valid badges provided."))
                return 


            reverse_map ={emoji :key for key ,emoji in badge_emojis .items ()}

            if user_badge :

                existing_emojis =user_badge ['badge_count'].split ()
                existing_keys =[]
                for em in existing_emojis :
                    key =reverse_map .get (em )
                    if key :
                        existing_keys .append (key )


                for badge in valid_input_keys :
                    if badge in badge_order_numerics :

                        if badge in existing_keys :
                            existing_keys .remove (badge )
                        else :
                            existing_keys =[k for k in existing_keys if k not in badge_order_numerics ]
                            existing_keys .append (badge )
                    else :

                        if badge in existing_keys :
                            existing_keys .remove (badge )
                        else :
                            existing_keys .append (badge )


                updated_keys =[k for k in badge_order if k in existing_keys ]


                user_badge ['badge_count']=" ".join (badge_emojis [k ]for k in updated_keys )

            else :

                updated_keys =[k for k in badge_order if k in valid_input_keys ]
                new_emoji_string =" ".join (badge_emojis [k ]for k in updated_keys )
                badges .append ({'user_id':user .id ,'badge_count':new_emoji_string })



            self .save_badges (badges )


            badge_emojis_display =" ".join (badge_emojis [k ]for k in updated_keys )


            await self .send_congrats_dm (user ,badge_emojis_display )


            await ctx .send (embed =success_embed (
            f"Updated {user .display_name }'s badges to: {badge_emojis_display }"
            ))

        except Exception as e :
            await ctx .send (embed =error_embed (f"Error: {str (e )}"))


async def setup (bot ):

    await bot .add_cog (BadgeManagement (bot ))
