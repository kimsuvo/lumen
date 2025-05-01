import os 
import sqlite3 
from glob import glob 
from datetime import datetime ,timedelta ,timezone 
import discord 
from discord .ext import commands 
from discord import app_commands 



def is_user_premium (user_id :int )->bool :
    premium_db_dir ="premiumdatabase"
    db_files =sorted (glob (os .path .join (premium_db_dir ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM premium WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 

CREDENTIALS_DB_DIR ="credentialsdatabase"

def is_user_registered (user_id :int )->bool :
    db_files =sorted (glob (os .path .join (CREDENTIALS_DB_DIR ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()
            cursor .execute ("SELECT 1 FROM users WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 



class AutoFB (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 
        self .autofb_db_dir ="autofbdatabase"

        if not os .path .exists (self .autofb_db_dir ):
            os .makedirs (self .autofb_db_dir )


    def get_autofb_db_files (self ):
        pattern =os .path .join (self .autofb_db_dir ,"autofb_*.db")
        files =glob (pattern )
        files .sort (key =lambda x :int (os .path .splitext (os .path .basename (x ))[0 ].split ('_')[1 ]))
        return files 

    def create_table_if_not_exists (self ,db_path :str ):
        try :
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute (
            "CREATE TABLE IF NOT EXISTS autofb ("
            "user_id TEXT PRIMARY KEY, "
            "duration INTEGER, "
            "next_timestamp TEXT)"
            )
            conn .commit ()
        except sqlite3 .Error as e :
            print (f"Error creating table in {db_path }: {e }")
        finally :
            conn .close ()

    def get_entry_count (self ,db_path :str )->int :
        try :
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute ("SELECT COUNT(*) FROM autofb")
            count =c .fetchone ()[0 ]
            return count 
        except sqlite3 .Error as e :
            print (f"Error counting entries in {db_path }: {e }")
            return 0 
        finally :
            conn .close ()

    def find_user_in_dbs (self ,user_id :str ):
        db_files =self .get_autofb_db_files ()
        for db_file in db_files :
            self .create_table_if_not_exists (db_file )
            try :
                conn =sqlite3 .connect (db_file )
                c =conn .cursor ()
                c .execute ("SELECT * FROM autofb WHERE user_id = ?",(user_id ,))
                data =c .fetchone ()
                if data :
                    return db_file 
            except sqlite3 .Error as e :
                print (f"Error querying {db_file }: {e }")
            finally :
                conn .close ()
        return None 

    def update_user_entry (self ,db_path :str ,user_id :str ,duration :int ,next_timestamp :str ):
        try :
            conn =sqlite3 .connect (db_path )
            c =conn .cursor ()
            c .execute (
            "UPDATE autofb SET duration = ?, next_timestamp = ? WHERE user_id = ?",
            (duration ,next_timestamp ,user_id )
            )
            conn .commit ()
        except sqlite3 .Error as e :
            print (f"Error updating user entry in {db_path }: {e }")
            raise 
        finally :
            conn .close ()

    def insert_user_entry (self ,user_id :str ,duration :int ,next_timestamp :str ):
        db_files =self .get_autofb_db_files ()
        target_db =None 
        for db_file in db_files :
            self .create_table_if_not_exists (db_file )
            if self .get_entry_count (db_file )<5000 :
                target_db =db_file 
                break 

        if not target_db :
            new_db_index =1 
            if db_files :
                new_db_index =int (os .path .splitext (os .path .basename (db_files [-1 ]))[0 ].split ('_')[1 ])+1 
            target_db =os .path .join (self .autofb_db_dir ,f"autofb_{new_db_index }.db")
            self .create_table_if_not_exists (target_db )

        try :
            conn =sqlite3 .connect (target_db )
            c =conn .cursor ()
            c .execute (
            "INSERT OR REPLACE INTO autofb (user_id, duration, next_timestamp) VALUES (?, ?, ?)",
            (user_id ,duration ,next_timestamp )
            )
            conn .commit ()
        except sqlite3 .Error as e :
            print (f"Error inserting user entry in {target_db }: {e }")
            raise 
        finally :
            conn .close ()


    auto_group =app_commands .Group (name ="auto",description ="Auto commands")


    feedback_group =app_commands .Group (name ="feedback",description ="Feedback commands")

    @feedback_group .command (
    name ="mail",
    description ="Enable Auto Feedback Mail by providing days (1-365), or type 'no' to disable."
    )
    @app_commands .describe (days ="Enter number of days (1-365) to enable AutoFB, or 'no' to disable it")
    async def mail (self ,interaction :discord .Interaction ,days :str ):
        user_id =str (interaction .user .id )
        embed_color =0x000001 


        if not is_user_registered (interaction .user .id ):
            embed =discord .Embed (
            title ="Not Registered",
            description ="You must be registered to use this command.",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        if not is_user_premium (interaction .user .id ):
            embed =discord .Embed (
            title ="**Upgrade to Lumen Premium**",
            description ="This command is only available to premium users. Consider upgrading to Lumen Premium.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        premium_status =is_user_premium (interaction .user .id )


        if days .lower ()=="no":
            db_file =self .find_user_in_dbs (user_id )
            if db_file :
                try :
                    conn =sqlite3 .connect (db_file )
                    c =conn .cursor ()
                    c .execute ("DELETE FROM autofb WHERE user_id = ?",(user_id ,))
                    conn .commit ()
                except sqlite3 .Error as e :
                    print (f"Error deleting entry in {db_file }: {e }")
                    error_embed =discord .Embed (
                    title ="Error",
                    description ="There was an error turning off AutoFB. Please try again later.",
                    color =discord .Color .red ()
                    )
                    await interaction .response .send_message (embed =error_embed ,ephemeral =True )
                    return 
                finally :
                    conn .close ()

                embed =discord .Embed (
                title ="Auto Feedback Mail Disabled",
                description ="AutoFB has been turned off for you.",
                color =embed_color 
                )
                if premium_status :
                    embed .set_footer (text ="Premium User")
                await interaction .response .send_message (embed =embed )
            else :
                embed =discord .Embed (
                title ="Auto Feedback Mail Not Enabled",
                description ="You do not have AutoFB enabled.",
                color =embed_color 
                )
                if premium_status :
                    embed .set_footer (text ="Premium User")
                await interaction .response .send_message (embed =embed )
            return 


        try :
            day_count =int (days )
        except ValueError :
            embed =discord .Embed (
            title ="Invalid Argument",
            description ="Please enter a number between 1 and 365, or 'no' to disable.",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        if not 1 <=day_count <=365 :
            embed =discord .Embed (
            title ="Invalid Duration",
            description ="Duration must be between 1 and 365 days.",
            color =discord .Color .red ()
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        tz =timezone (timedelta (hours =5 ,minutes =30 ))
        current_time =datetime .now (tz )
        next_time =current_time +timedelta (days =day_count )
        next_timestamp =next_time .isoformat ()


        existing_db =self .find_user_in_dbs (user_id )
        if existing_db :
            self .update_user_entry (existing_db ,user_id ,day_count ,next_timestamp )
        else :
            self .insert_user_entry (user_id ,day_count ,next_timestamp )

        embed =discord .Embed (
        title ="Auto Feedback Mail Enabled",
        description =f"AutoFB has been set for **{day_count }** days.",
        color =embed_color 
        )
        if premium_status :
            embed .set_footer (text ="Premium User")
        await interaction .response .send_message (embed =embed )


    auto_group .add_command (feedback_group )



async def setup (bot :commands .Bot ):

    cog =AutoFB (bot )
    await bot .add_cog (cog )
    existing =bot .tree .get_command ("auto")
    if not existing :
        bot .tree .add_command (cog .auto_group )

