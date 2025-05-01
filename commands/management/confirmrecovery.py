import discord 
from discord .ext import commands 
import sqlite3 
import bcrypt 
import aiohttp 

import os 
from config import RECOVERY_STAFF_ROLE_ID ,RECOVERY_CONFIRM_CHANNEL_ID 

class ConfirmRecovery (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="confirmrecovery")
    async def confirm_recovery (self ,ctx ,recovery_id :str ):

        if not any (role .id in RECOVERY_STAFF_ROLE_ID for role in ctx .author .roles ):
            await ctx .send ("You do not have permission to perform this action.",delete_after =10 )
            return 


        database_directories ={
        "credentials":"credentialsdatabase",
        "products":"productsdatabase",
        "badges":"badgesdatabase",
        "images":"imagedatabase",
        "feedback_count":"feedbackcountdatabase",
        "feedback":"feedbackdatabase",
        "status":"statusdatabase",
        "blacklists":"blacklistsdatabase",
        "verification":"verificationdatabase",
        "pending_feedback":"pendingfeedbackdatabase",
        "warnings":"warningsdatabase",
        "info":"infodatabase",
        "rejected_feedbacks":"rejectedfeedbacks",
        "recovery":"recoverydatabase",
        "premium_users":"premiumdatabase",
        "premiumfeedback":"premiumpendingfeedback",
        "premiumverificationfeedback":"premiumverificationfeedback",
        "color":"colordatabase",
        "buttons":"buttonsdatabase",
        "autofb":"autofbdatabase",
        "custombutton":"custombuttondatabase",
        "tickuser":"verifiedusers"

        }




        recovery_data =None 
        recovery_db_dir =database_directories ["recovery"]
        for db_file in os .listdir (recovery_db_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (recovery_db_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "SELECT previous_user_id, new_user_id, username, password FROM pending_recovery WHERE recovery_id = ?",
                    (recovery_id ,)
                    )
                    result =cursor .fetchone ()
                    if result :
                        recovery_data =result 
                        break 
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error accessing `{db_file }` in recoverydatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await ctx .send (embed =error_embed )
                    return 
                finally :
                    conn .close ()

        if not recovery_data :
            initial_embed =discord .Embed (
            title ="**Profile Recovery Failed**",
            description ="Invalid recovery ID. Please check and try again.",
            color =0xFF0000 ,
            )
            initial_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
            await ctx .send (embed =initial_embed )
            return 

        previous_user_id ,new_user_id ,username ,password =recovery_data 


        initial_embed =discord .Embed (
        title ="**Profile Recovery in Progress**",
        description =f"Recovering profile for new user ID `{new_user_id }`...",
        color =0xFF9900 ,
        )
        initial_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
        initial_embed .set_footer (text ="Please wait while the process is ongoing.")
        recovery_message =await ctx .send (embed =initial_embed )




        user =None 
        credentials_dir =database_directories ["credentials"]
        for db_file in os .listdir (credentials_dir ):
            if db_file .endswith (".db"):
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


                    cursor .execute ("SELECT * FROM users")
                    results =cursor .fetchall ()
                    for result in results :
                        stored_username_hash =result [1 ]

                        if bcrypt .checkpw (username .encode (),stored_username_hash .encode ()):
                            user =result 
                            break 
                    if user :
                        break 
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error accessing `{db_file }` in credentialsdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()

        if not user :
            error_embed =discord .Embed (
            title ="**Profile Recovery Failed**",
            description ="User validation failed. No matching user found in credentialsdatabase.",
            color =0xFF0000 ,
            )
            error_embed .add_field (name ="**Username**",value =username ,inline =False )
            error_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
            await recovery_message .edit (embed =error_embed )
            return 





        stored_hashed_password =user [2 ]
        if not stored_hashed_password :
            error_embed =discord .Embed (
            title ="**Profile Recovery Failed**",
            description ="No password found for the user in the database.",
            color =0xFF0000 ,
            )
            error_embed .add_field (name ="**Username**",value =username ,inline =False )
            error_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
            await recovery_message .edit (embed =error_embed )
            return 

        if not bcrypt .checkpw (password .encode (),stored_hashed_password .encode ()):
            error_embed =discord .Embed (
            title ="**Profile Recovery Failed**",
            description ="Password verification failed. Please provide the correct credentials.",
            color =0xFF0000 ,
            )
            error_embed .add_field (name ="**Username**",value =username ,inline =False )
            error_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
            await recovery_message .edit (embed =error_embed )
            return 




        if str (user [0 ])!=previous_user_id :
            error_embed =discord .Embed (
            title ="**Profile Recovery Failed**",
            description ="Previous user ID mismatch in credentialsdatabase.",
            color =0xFF0000 ,
            )
            error_embed .add_field (name ="**Expected User ID**",value =previous_user_id ,inline =False )
            error_embed .add_field (name ="**Found User ID**",value =user [0 ],inline =False )
            error_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
            await recovery_message .edit (embed =error_embed )
            return 







        databases_to_check =[
        ("credentials","users","user_id"),
        ("products","services_and_products","user_id"),
        ("badges","badges","user_id"),
        ("images","imagethumbnail","user_id"),
        ("feedback_count","feedback_count","receiver_id"),
        ("status","statuses","user_id"),
        ("blacklists","blacklists","user_id"),
        ("verification","pending_feedback","receiver_id"),
        ("pending_feedback","pending_feedback","receiver_id"),
        ("warnings","warnings","user_id"),
        ("info","cpinfo","user_id"),
        ("rejected_feedbacks","rejected_feedback","receiver_id"),
        ("premium_users","premium","user_id"),
        ("premiumfeedback","pending_feedback","receiver_id"),
        ("premiumverificationfeedback","pending_feedback","receiver_id"),
        ("color","colors","user_id"),
        ("buttons","buttons","user_id"),
        ("custombutton","custombuttons","user_id"),
        ("tickuser","verified","user_id"),
        ("autofb","autofb","user_id")
        ]

        for key ,table ,column in databases_to_check :
            db_dir =database_directories [key ]
            for db_file in os .listdir (db_dir ):
                if db_file .endswith (".db"):
                    db_path =os .path .join (db_dir ,db_file )
                    try :
                        conn =sqlite3 .connect (db_path )
                        cursor =conn .cursor ()

                        if key =="feedback":

                            table_name =f"feedback_{new_user_id }"
                            cursor .execute ("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table_name ,))
                            if cursor .fetchone ():
                                error_embed =discord .Embed (
                                title ="**Profile Recovery Failed**",
                                description =f"Feedback table `{table_name }` already exists in `{db_file }`.",
                                color =0xFF0000 ,
                                )
                                await recovery_message .edit (embed =error_embed )
                                return 
                        else :
                            query =f"SELECT 1 FROM {table } WHERE {column } = ?"
                            cursor .execute (query ,(new_user_id ,))
                            if cursor .fetchone ():
                                error_embed =discord .Embed (
                                title ="**Profile Recovery Failed**",
                                description =f"New User ID `{new_user_id }` already exists in table `{table }` in `{db_file }`.",
                                color =0xFF0000 ,
                                )
                                await recovery_message .edit (embed =error_embed )
                                return 
                    except sqlite3 .Error as e :
                        error_embed =discord .Embed (
                        title ="**Profile Recovery Failed**",
                        description =f"Error checking `{db_file }` in {key } database.",
                        color =0xFF0000 ,
                        )
                        error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                        await recovery_message .edit (embed =error_embed )
                        return 
                    finally :
                        conn .close ()






        for db_file in os .listdir (credentials_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (credentials_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "UPDATE users SET user_id = ? WHERE user_id = ?",
                    (new_user_id ,previous_user_id )
                    )
                    conn .commit ()
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in credentialsdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()






        await recovery_message .edit (embed =discord .Embed (
        title ="**Credentials Updated**",
        description =f"User ID updated from `{previous_user_id }` to `{new_user_id }` in credentialsdatabase.",
        color =0x00FF00 
        ))






        products_dir =database_directories ["products"]
        for db_file in os .listdir (products_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (products_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM services_and_products WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE services_and_products SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No data found in `{db_file }` for user ID: `{previous_user_id }` in productsdatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in productsdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        badges_dir =database_directories ["badges"]
        for db_file in os .listdir (badges_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (badges_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM badges WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():

                        cursor .execute ("SELECT 1 FROM badges WHERE user_id = ?",(new_user_id ,))
                        if not cursor .fetchone ():
                            cursor .execute (
                            "UPDATE badges SET user_id = ? WHERE user_id = ?",
                            (new_user_id ,previous_user_id )
                            )
                            conn .commit ()
                        else :
                            warning_embed =discord .Embed (
                            title ="**Profile Recovery Warning**",
                            description =f"User `{new_user_id }` already exists in `{db_file }` in badgesdatabase. Skipping update.",
                            color =0xFFFF00 ,
                            )
                            await recovery_message .edit (embed =warning_embed )
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No data found in `{db_file }` for user ID: `{previous_user_id }` in badgesdatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in badgesdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        images_dir =database_directories ["images"]
        for db_file in os .listdir (images_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (images_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM imagethumbnail WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():

                        cursor .execute ("DELETE FROM imagethumbnail WHERE user_id = ?",(new_user_id ,))
                        conn .commit ()

                        cursor .execute (
                        "INSERT INTO imagethumbnail (user_id, thumbnail, image, DWC) "
                        "SELECT ?, thumbnail, image, DWC FROM imagethumbnail WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()

                        cursor .execute ("DELETE FROM imagethumbnail WHERE user_id = ?",(previous_user_id ,))
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No data found in `{db_file }` for user ID: `{previous_user_id }` in imagedatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in imagedatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        feedback_count_dir =database_directories ["feedback_count"]
        for db_file in os .listdir (feedback_count_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (feedback_count_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute ("""
                        CREATE TABLE IF NOT EXISTS feedback_count (
                            receiver_id TEXT PRIMARY KEY,
                            total_feedback_count INTEGER,
                            positive_feedback_count INTEGER,
                            negative_feedback_count INTEGER
                        )
                    """)
                    conn .commit ()
                    cursor .execute ("SELECT 1 FROM feedback_count WHERE receiver_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE feedback_count SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No feedback count data found in `{db_file }` for user ID: `{previous_user_id }`. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in feedbackcountdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        feedback_dir =database_directories ["feedback"]
        for db_file in os .listdir (feedback_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (feedback_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    table_name_old =f"feedback_{previous_user_id }"
                    table_name_new =f"feedback_{new_user_id }"
                    cursor .execute (
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name_old ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        f"ALTER TABLE {table_name_old } RENAME TO {table_name_new }"
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"Feedback table `{table_name_old }` not found in `{db_file }`. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in feedbackdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        status_dir =database_directories ["status"]
        for db_file in os .listdir (status_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (status_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ('''
                        CREATE TABLE IF NOT EXISTS statuses (
                            user_id INTEGER PRIMARY KEY,
                            status TEXT,
                            status_update_block TEXT
                        )
                    ''')
                    conn .commit ()
                    cursor .execute ("SELECT 1 FROM statuses WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE statuses SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No status data found in `{db_file }` for user ID: `{previous_user_id }`. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in statusdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        blacklists_dir =database_directories ["blacklists"]
        for db_file in os .listdir (blacklists_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (blacklists_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM blacklists WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE blacklists SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No blacklist data found in `{db_file }` for user ID: `{previous_user_id }`. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in blacklistsdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        verification_dir =database_directories ["verification"]
        for db_file in os .listdir (verification_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (verification_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM pending_feedback WHERE receiver_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE pending_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No pending feedback found in `{db_file }` for receiver ID: `{previous_user_id }` in verificationdatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in verificationdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        pending_feedback_dir =database_directories ["pending_feedback"]
        for db_file in os .listdir (pending_feedback_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (pending_feedback_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM pending_feedback WHERE receiver_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE pending_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No pending feedback found in `{db_file }` for receiver ID: `{previous_user_id }` in pendingfeedbackdatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in pendingfeedbackdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        warnings_dir =database_directories ["warnings"]
        for db_file in os .listdir (warnings_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (warnings_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM warnings WHERE user_id = ?",(previous_user_id ,))
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE warnings SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        warning_embed =discord .Embed (
                        title ="**Profile Recovery Warning**",
                        description =f"No warnings data found in `{db_file }` for user ID: `{previous_user_id }` in warningsdatabase. Skipping...",
                        color =0xFFFF00 ,
                        )
                        await recovery_message .edit (embed =warning_embed )
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in warningsdatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        info_dir =database_directories ["info"]
        for db_file in os .listdir (info_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (info_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()

                    cursor .execute (
                    "UPDATE cpinfo SET user_id = ? WHERE user_id = ?",
                    (new_user_id ,previous_user_id )
                    )
                    conn .commit ()
                except sqlite3 .Error as e :
                    error_embed =discord .Embed (
                    title ="**Profile Recovery Failed**",
                    description =f"Error updating `{db_file }` in infodatabase.",
                    color =0xFF0000 ,
                    )
                    error_embed .add_field (name ="**Error**",value =str (e ),inline =False )
                    await recovery_message .edit (embed =error_embed )
                    return 
                finally :
                    conn .close ()


        rejected_dir =database_directories ["rejected_feedbacks"]
        for db_file in os .listdir (rejected_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (rejected_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM rejected_feedback WHERE receiver_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE rejected_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No rejected feedback entry in {db_file } for receiver_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in rejectedfeedbacks `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()


        premium_dir =database_directories ["premium_users"]
        for db_file in os .listdir (premium_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (premium_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM premium WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE premium SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No premium entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in premium_users `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()


        premiumfeedback_dir =database_directories ["premiumfeedback"]
        for db_file in os .listdir (premiumfeedback_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (premiumfeedback_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM pending_feedback WHERE receiver_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE pending_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No premium feedback entry in {db_file } for receiver_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in premium_users `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        premiumverifyfeedback_dir =database_directories ["premiumverificationfeedback"]
        for db_file in os .listdir (premiumverifyfeedback_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (premiumverifyfeedback_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM pending_feedback WHERE receiver_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE pending_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No premium verification feedback entry in {db_file } for receiver_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in premiumverificationfeedback `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        premiumverifyfeedback_dir =database_directories ["premiumverificationfeedback"]
        for db_file in os .listdir (premiumverifyfeedback_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (premiumverifyfeedback_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM pending_feedback WHERE receiver_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE pending_feedback SET receiver_id = ? WHERE receiver_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No premium verification feedback entry in {db_file } for receiver_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in premium_verification_fb `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        color_dir =database_directories ["color"]
        for db_file in os .listdir (color_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (color_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM colors WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE colors SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No colors entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in colors `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        button_dir =database_directories ["buttons"]
        for db_file in os .listdir (button_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (button_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM buttons WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE buttons SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No buttons entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in buttons `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        custombutton_dir =database_directories ["custombutton"]
        for db_file in os .listdir (custombutton_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (custombutton_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM custombuttons WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE custombuttons SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No custom buttons entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in custom buttons `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()


        tickuser_dir =database_directories ["tickuser"]
        for db_file in os .listdir (tickuser_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (tickuser_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM verified WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE verified SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No verified entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in verified `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()



        autofb_dir =database_directories ["autofb"]
        for db_file in os .listdir (autofb_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (autofb_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute (
                    "SELECT 1 FROM autofb WHERE user_id = ?",
                    (previous_user_id ,)
                    )
                    if cursor .fetchone ():
                        cursor .execute (
                        "UPDATE autofb SET user_id = ? WHERE user_id = ?",
                        (new_user_id ,previous_user_id )
                        )
                        conn .commit ()
                    else :
                        print (f"No autofb entry in {db_file } for user_id: {previous_user_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in autofb `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()







        recovery_dir =database_directories ["recovery"]
        for db_file in os .listdir (recovery_dir ):
            if db_file .endswith (".db"):
                db_path =os .path .join (recovery_dir ,db_file )
                try :
                    conn =sqlite3 .connect (db_path )
                    cursor =conn .cursor ()
                    cursor .execute ("SELECT 1 FROM pending_recovery WHERE recovery_id = ?",(recovery_id ,))
                    if cursor .fetchone ():
                        cursor .execute ("DELETE FROM pending_recovery WHERE recovery_id = ?",(recovery_id ,))
                        conn .commit ()
                    else :
                        print (f"No recovery entry found in `{db_file }` for recovery ID: {recovery_id }. Skipping...")
                except sqlite3 .Error as e :
                    print (f"Database error in recoverydatabase `{db_file }`: {e }")
                    return 
                finally :
                    conn .close ()




        log_embed =discord .Embed (
        title ="**Profile Recovery Confirmed**",
        description ="A recovery request has been approved.",
        color =0x000001 ,
        timestamp =discord .utils .utcnow (),
        )
        log_embed .add_field (name ="**Confirmed By**",value =ctx .author .mention ,inline =True )
        log_embed .add_field (name ="**New User ID**",value =new_user_id ,inline =True )
        log_embed .add_field (name ="**New User Mention**",value =f"<@{new_user_id }>",inline =True )
        log_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =True )
        log_embed .add_field (name ="**Timestamp**",value =discord .utils .format_dt (discord .utils .utcnow (),style ='F'),inline =True )

        channel =ctx .bot .get_channel (RECOVERY_CONFIRM_CHANNEL_ID )
        if channel :
            await channel .send (embed =log_embed )
        else :
            await ctx .send ("Error: Recovery confirmation channel not found.")


        try :
            new_user =ctx .bot .get_user (int (new_user_id ))
            if new_user :
                dm_embed =discord .Embed (
                title ="**Profile Recovery Approved**",
                description ="Your recovery request has been successfully approved.",
                color =0x000001 ,
                )
                dm_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
                dm_embed .set_footer (text ="Thank you for your patience.")
                await new_user .send (embed =dm_embed )
        except discord .Forbidden :
            print (f"Failed to DM user {new_user_id } about recovery approval.")

        final_success_embed =discord .Embed (
        title ="**Profile Recovery Completed**",
        description =f"User ID updated from `{previous_user_id }` to `{new_user_id }` successfully.",
        color =0x000001 ,
        )
        final_success_embed .add_field (name ="**Recovery ID**",value =recovery_id ,inline =False )
        final_success_embed .set_footer (text ="Recovery process completed successfully.")
        await recovery_message .edit (embed =final_success_embed )

        print (f"Profile recovery completed: Previous User ID: {previous_user_id }, New User ID: {new_user_id }, Recovery ID: {recovery_id }")

async def setup (bot ):
    await bot .add_cog (ConfirmRecovery (bot ))
