import discord 
from discord .ext import commands 
import sqlite3 
import os 
from config import DEV_CHAMBER_ROLE ,DEV_CHAMBER_GUILD_ID ,DELETION_PASSWORD 


BADGESDATABASE_DIR =os .path .join (os .getcwd (),"badgesdatabase")
BLACKLISTSDATABASE_DIR =os .path .join (os .getcwd (),"blacklistsdatabase")
CREDENTIALSDATABASE_DIR =os .path .join (os .getcwd (),"credentialsdatabase")
IMAGEDATABASE_DIR =os .path .join (os .getcwd (),"imagedatabase")
PRODUCTSDATABASE_DIR =os .path .join (os .getcwd (),"productsdatabase")
STATUSDATABASE_DIR =os .path .join (os .getcwd (),"statusdatabase")
WARNINGSDATABASE_DIR =os .path .join (os .getcwd (),"warningsdatabase")
RECOVERYDATABASE_DIR =os .path .join (os .getcwd (),"recoverydatabase")
FEEDBACKDATABASE_DIR =os .path .join (os .getcwd (),"feedbackdatabase")
COLORDATABASE_DIR =os .path .join (os .getcwd (),"colordatabase")
REJECTEDFEEDBACKS_DIR =os .path .join (os .getcwd (),"rejectedfeedbacks")
FEEDBACKCOUNT_DIR =os .path .join (os .getcwd (),"feedbackcountdatabase")
PENDINGFEEDBACK_DIR =os .path .join (os .getcwd (),"pendingfeedbackdatabase")
VERIFICATIONFEEDBACK_DIR =os .path .join (os .getcwd (),"verificationdatabase")
PREMIUMUSER_DIR =os .path .join (os .getcwd (),"premiumdatabase")
FBINFO_DIR =os .path .join (os .getcwd (),"infodatabase")
PREMIUMFEEDBACK_DIR =os .path .join (os .getcwd (),"premiumpendingfeedback")
PREMIUMVERIFICATIONFEEDBACK_DIR =os .path .join (os .getcwd (),"premiumverificationfeedback")
BANNED_DIR =os .path .join (os .getcwd (),"bandatabase")
BUTTONS_DIR =os .path .join (os .getcwd (),"buttonsdatabase")
AUTOFB_DIR =os .path .join (os .getcwd (),"autofbdatabase")
CUSTOMBUTTON_DIR =os .path .join (os .getcwd (),"custombuttondatabase")
TICK_DIR =os .path .join (os .getcwd (),"verifiedusers")

class DeleteUserCog (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    def delete_user_data (self ,user_id :str ):

        for filename in os .listdir (BADGESDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (BADGESDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM badges WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (BLACKLISTSDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (BLACKLISTSDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM blacklists WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (CREDENTIALSDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (CREDENTIALSDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM users WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (IMAGEDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (IMAGEDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM imagethumbnail WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (PRODUCTSDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (PRODUCTSDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM services_and_products WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (STATUSDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (STATUSDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM statuses WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (WARNINGSDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (WARNINGSDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM warnings WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (RECOVERYDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (RECOVERYDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute (
                "DELETE FROM pending_recovery WHERE previous_user_id = ? OR new_user_id = ?",
                (user_id ,user_id )
                )
                conn .commit ()
                conn .close ()



        for filename in os .listdir (FEEDBACKDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (FEEDBACKDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                table_name =f"feedback_{user_id }"
                cursor .execute (f"DROP TABLE IF EXISTS {table_name }")
                conn .commit ()
                conn .close ()


        for filename in os .listdir (COLORDATABASE_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (COLORDATABASE_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM colors WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (FEEDBACKCOUNT_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (FEEDBACKCOUNT_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM feedback_count WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (PENDINGFEEDBACK_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (PENDINGFEEDBACK_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM pending_feedback WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (VERIFICATIONFEEDBACK_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (VERIFICATIONFEEDBACK_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM pending_feedback WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



        for filename in os .listdir (REJECTEDFEEDBACKS_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (REJECTEDFEEDBACKS_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM rejected_feedback WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (PREMIUMFEEDBACK_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (PREMIUMFEEDBACK_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM pending_feedback WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (PREMIUMVERIFICATIONFEEDBACK_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (PREMIUMVERIFICATIONFEEDBACK_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM pending_feedback WHERE receiver_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



        for filename in os .listdir (PREMIUMUSER_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (PREMIUMUSER_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM premium WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



        for filename in os .listdir (FBINFO_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (FBINFO_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM cpinfo WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



        for filename in os .listdir (BANNED_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (BANNED_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM banned WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (BUTTONS_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (BUTTONS_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM buttons WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



        for filename in os .listdir (AUTOFB_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (AUTOFB_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM autofb WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (CUSTOMBUTTON_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (CUSTOMBUTTON_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM custombuttons WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()


        for filename in os .listdir (TICK_DIR ):
            if filename .endswith (".db"):
                db_path =os .path .join (TICK_DIR ,filename )
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("DELETE FROM verified WHERE user_id = ?",(user_id ,))
                conn .commit ()
                conn .close ()



    def log_deletion (self ,interaction :discord .Interaction ,user_id :str ):
        with open ("deletion_log.txt","a")as log_file :
            log_file .write (
            f"User {user_id } was deleted by {interaction .user } (ID: {interaction .user .id }) "
            f"in guild {interaction .guild .name } (ID: {interaction .guild .id }) at {interaction .created_at }\n"
            )

    class ConfirmationView (discord .ui .View ):
        def __init__ (self ,cog ,user_id :str ,author_id :int ,timeout :float =60 ):
            super ().__init__ (timeout =timeout )
            self .cog =cog 
            self .user_id =user_id 
            self .author_id =author_id 

        async def interaction_check (self ,interaction :discord .Interaction )->bool :

            if interaction .user .id !=self .author_id :
                await interaction .response .send_message ("You are not allowed to interact with this.",ephemeral =True )
                return False 
            return True 

        async def disable_buttons (self ,interaction :discord .Interaction ):

            for item in self .children :
                if isinstance (item ,discord .ui .Button ):
                    item .disabled =True 
            await interaction .message .edit (view =self )
            self .stop ()

        @discord .ui .button (label ="CONFIRM",style =discord .ButtonStyle .success )
        async def confirm (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
            await self .disable_buttons (interaction )

            in_progress_embed =discord .Embed (
            title ="User Deletion Confirmation",
            description =f"Deletion confirmed for user ID: `{self .user_id }`.\nDeleting...",
            color =discord .Color .green ()
            )

            await interaction .response .defer ()
            second_message =await interaction .followup .send (embed =in_progress_embed ,wait =True )
            try :
                await interaction .delete_original_message ()
            except Exception :
                pass 

            try :
                self .cog .delete_user_data (self .user_id )
                self .cog .log_deletion (interaction ,self .user_id )

                success_embed =discord .Embed (
                title ="User Deletion Successful",
                description =f"Successfully deleted all data for user ID: `{self .user_id }`.",
                color =0x000001 
                )
                await second_message .edit (embed =success_embed )
            except Exception as e :
                error_embed =discord .Embed (
                title ="Error",
                description =f"An error occurred while deleting user data: `{e }`",
                color =discord .Color .red ()
                )
                await second_message .edit (embed =error_embed )

        @discord .ui .button (label ="DECLINE",style =discord .ButtonStyle .red )
        async def decline (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
            await self .disable_buttons (interaction )

            cancel_embed =discord .Embed (
            title ="User Deletion Cancelled",
            description =f"Deletion process for user ID: `{self .user_id }` has been cancelled.",
            color =discord .Color .blue ()
            )
            await interaction .response .send_message (embed =cancel_embed )
            try :
                await interaction .delete_original_message ()
            except Exception :
                pass 

            self .stop ()


    @discord .app_commands .command (name ="delete_user",description ="Delete the users database.")
    @discord .app_commands .guilds (discord .Object (id =DEV_CHAMBER_GUILD_ID ))
    async def delete_user (self ,interaction :discord .Interaction ,user_id :str ,password :str ):

        if DEV_CHAMBER_ROLE not in [role .id for role in interaction .user .roles ]:
            await interaction .response .send_message ("You do not have the required permissions to execute this command.",ephemeral =True )
            return 


        if password !=DELETION_PASSWORD :
            await interaction .response .send_message ("Invalid password.",ephemeral =True )
            return 


        try :
            target_user =await interaction .client .fetch_user (int (user_id ))
            target_username =target_user .name 
        except Exception :
            target_username ="Unknown"


        confirm_embed =discord .Embed (
        title ="User Deletion Confirmation",
        description =(
        f"Do you really want to delete all data for the following user?\n"
        f"**User ID:** `{user_id }`\n"
        f"**Username:** `{target_username }`"
        ),
        color =0x000001 
        )
        confirm_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=679f46d4&is=679df554&hm=d06244e816b6313e972c32884707e28f56c7bb6db764b212f541130b5cdeb4e5&=&format=webp&quality=lossless&width=670&height=670")


        view =DeleteUserCog .ConfirmationView (cog =self ,user_id =user_id ,author_id =interaction .user .id )


        await interaction .response .send_message (embed =confirm_embed ,view =view )


async def setup (bot ):
    await bot .add_cog (DeleteUserCog (bot ))
