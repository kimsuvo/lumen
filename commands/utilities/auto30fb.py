import os 
import time 
import sqlite3 
from glob import glob 
from datetime import datetime ,timedelta ,timezone 
import discord 
from discord .ext import commands 



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



class PreAutoFB (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 
        self .autofb_db_dir ="autofbdatabase"

        if not os .path .exists (self .autofb_db_dir ):
            os .makedirs (self .autofb_db_dir )

    def get_autofb_db_files (self ):
        """Return a sorted list of autofb database file paths."""
        pattern =os .path .join (self .autofb_db_dir ,"autofb_*.db")
        files =glob (pattern )

        files .sort (key =lambda x :int (os .path .splitext (os .path .basename (x ))[0 ].split ('_')[1 ]))
        return files 

    def create_table_if_not_exists (self ,db_path :str ):
        """Ensure that the autofb table exists in the given database."""
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
        """Return the number of entries in the autofb table for the given database."""
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
        """
        Look for the user's entry in all autofb databases.
        Returns the path of the database file if found, otherwise None.
        """
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
        """Update an existing autofb entry for the user."""
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
        """
        Insert a new entry into the first autofb database that has fewer than 5000 entries.
        If none exist, create a new database file.
        """
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

    @commands .command (name ="autofb")
    async def autofb (self ,ctx :commands .Context ,arg :str ):
        """
        Command usage:
          +autofb <days from 1-365/off>
        Examples:
          +autofb 7      -> Enables AutoFB for 7 days.
          +autofb off    -> Disables AutoFB.
        """
        user_id =str (ctx .author .id )
        embed_color =0x000001 

        try :

            if not is_user_registered (ctx .author .id ):
                embed =discord .Embed (
                title ="Not Registered",
                description ="You must be registered to use this command.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            if not is_user_premium (ctx .author .id ):
                embed =discord .Embed (
                title ="**Upgrade to Lumen Premium**",
                description ="This command is only available to premium users. Consider upgrading to Lumen Premium.",
                color =0xff0000 
                )
                await ctx .send (embed =embed )
                return 



            premium_status =is_user_premium (ctx .author .id )


            if arg .lower ()=="off":
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
                        await ctx .send (embed =error_embed )
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
                    await ctx .send (embed =embed )
                else :
                    embed =discord .Embed (
                    title ="Auto Feedback Mail Not Enabled",
                    description ="You do not have AutoFB enabled.",
                    color =embed_color 
                    )
                    if premium_status :
                        embed .set_footer (text ="Premium User")
                    await ctx .send (embed =embed )
                return 


            try :
                days =int (arg )
            except ValueError :
                embed =discord .Embed (
                title ="Invalid Argument",
                description ="Please enter a number between 1 and 365, or 'off'.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 

            if not 1 <=days <=365 :
                embed =discord .Embed (
                title ="Invalid Duration",
                description ="Duration must be between 1 and 365 days.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 



            tz =timezone (timedelta (hours =5 ,minutes =30 ))
            current_time =datetime .now (tz )
            next_time =current_time +timedelta (days =days )
            next_timestamp =next_time .isoformat ()


            existing_db =self .find_user_in_dbs (user_id )
            if existing_db :
                self .update_user_entry (existing_db ,user_id ,days ,next_timestamp )
            else :
                self .insert_user_entry (user_id ,days ,next_timestamp )

            embed =discord .Embed (
            title ="Auto Feedback Mail Enabled",
            description =f"AutoFB has been set for **{days }** days.",
            color =embed_color 
            )
            if premium_status :
                embed .set_footer (text ="Premium User")
            await ctx .send (embed =embed )

        except Exception as e :
            print (f"Unexpected error in autofb command: {e }")
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred. Please try again later.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed )



    @commands .command (name ="autofb_test")
    async def autofb_test (self ,ctx :commands .Context ,arg :str ):
        """
        Testing command usage:
          +autofb_test <minutes from 1-10/off>
        Examples:
          +autofb_test 5   -> Enables AutoFB for 5 minutes (testing mode).
          +autofb_test off -> Disables AutoFB (testing mode).
        """
        user_id =str (ctx .author .id )
        embed_color =0x000001 

        try :

            if not is_user_registered (ctx .author .id ):
                embed =discord .Embed (
                title ="Not Registered",
                description ="You must be registered to use this command.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 

            premium_status =is_user_premium (ctx .author .id )


            if arg .lower ()=="off":
                db_file =self .find_user_in_dbs (user_id )
                if db_file :
                    try :
                        conn =sqlite3 .connect (db_file )
                        c =conn .cursor ()
                        c .execute ("DELETE FROM autofb WHERE user_id = ?",(user_id ,))
                        conn .commit ()
                    except sqlite3 .Error as e :
                        print (f"Error deleting test entry in {db_file }: {e }")
                        error_embed =discord .Embed (
                        title ="Error",
                        description ="There was an error turning off AutoFB testing mode. Please try again later.",
                        color =discord .Color .red ()
                        )
                        await ctx .send (embed =error_embed )
                        return 
                    finally :
                        conn .close ()

                    embed =discord .Embed (
                    title ="Test Auto Feedback Mail Disabled",
                    description ="AutoFB testing mode has been turned off for you.",
                    color =embed_color 
                    )
                    if premium_status :
                        embed .set_footer (text ="Premium User")
                    await ctx .send (embed =embed )
                else :
                    embed =discord .Embed (
                    title ="Test Auto Feedback Mail Not Enabled",
                    description ="You do not have AutoFB testing mode enabled.",
                    color =embed_color 
                    )
                    if premium_status :
                        embed .set_footer (text ="Premium User")
                    await ctx .send (embed =embed )
                return 


            try :
                minutes =int (arg )
            except ValueError :
                embed =discord .Embed (
                title ="Invalid Argument",
                description ="Please enter a number between 1 and 10, or 'off'.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 

            if not 1 <=minutes <=10 :
                embed =discord .Embed (
                title ="Invalid Duration",
                description ="Testing duration must be between 1 and 10 minutes.",
                color =discord .Color .red ()
                )
                await ctx .send (embed =embed )
                return 


            tz =timezone (timedelta (hours =5 ,minutes =30 ))
            current_time =datetime .now (tz )
            next_time =current_time +timedelta (minutes =minutes )
            next_timestamp =next_time .isoformat ()


            existing_db =self .find_user_in_dbs (user_id )
            if existing_db :
                self .update_user_entry (existing_db ,user_id ,minutes ,next_timestamp )
            else :
                self .insert_user_entry (user_id ,minutes ,next_timestamp )

            embed =discord .Embed (
            title ="Test Auto Feedback Mail Enabled",
            description =f"AutoFB testing mode has been set for **{minutes }** minutes.",
            color =embed_color 
            )
            if premium_status :
                embed .set_footer (text ="Premium User")
            await ctx .send (embed =embed )

        except Exception as e :
            print (f"Unexpected error in autofb_test command: {e }")
            error_embed =discord .Embed (
            title ="Unexpected Error",
            description ="An unexpected error occurred in testing mode. Please try again later.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed )





async def setup (bot :commands .Bot ):
    await bot .add_cog (PreAutoFB (bot ))


