
import discord 
from discord .ext import commands 
import sqlite3 
import logging 
from datetime import datetime 
import pytz 
import glob 
import os 
from config import RECOVERY_STAFF_ROLE_ID ,RECOVERY_REJECT_CHANNEL_ID 

class RejectRecovery (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .command (name ="rejectrecovery")
    async def reject_recovery (self ,ctx ,recovery_id :str ,*,reason :str ):

        if not any (role .id in RECOVERY_STAFF_ROLE_ID for role in ctx .author .roles ):
            embed =discord .Embed (
            title ="Permission Denied",
            description ="You do not have the required permissions to run this command.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 



        if not reason :
            embed =discord .Embed (
            title ="Missing Reason",
            description ="You must provide a reason for rejecting the recovery.",
            color =0xff0000 
            )
            await ctx .send (embed =embed )
            return 


        processing_embed =discord .Embed (
        title ="<a:lumen_loading:1326260453260656735> **Rejecting Recovery Request**",
        description =f"Processing the rejection of recovery request `{recovery_id }`...",
        color =0x000001 
        )
        message =await ctx .send (embed =processing_embed )

        steps_status =[]
        steps_status .append ("**Recovery Rejected**")


        recovery_data =None 


        db_found =False 
        db_files =glob .glob (os .path .join ("recoverydatabase","*.db"))
        if not db_files :
            error_embed =discord .Embed (
            title ="Database Error",
            description ="No database files found in the 'recoverydatabase' directory.",
            color =0xff0000 
            )
            await message .edit (embed =error_embed )
            return 

        for db_file in db_files :
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()

                cursor .execute ('SELECT * FROM pending_recovery WHERE recovery_id = ?;',(recovery_id ,))
                data =cursor .fetchone ()

                if data :
                    db_found =True 
                    recovery_data =data 
                    steps_status .append (f"<:lumen_online:1326260453260656735> Fetched recovery data from `{os .path .basename (db_file )}`.")



                    recovery_id ,previous_user_id ,new_user_id ,email ,_ =recovery_data 


                    cursor .execute ('DELETE FROM pending_recovery WHERE recovery_id = ?;',(recovery_id ,))
                    conn .commit ()
                    steps_status .append (f"<:lumen_online:1326260453260656735> Deleted recovery request from `{os .path .basename (db_file )}`.")
                    break 

            except Exception as e :
                error_message =f"Error while processing database `{os .path .basename (db_file )}`: {e }"
                logging .error (error_message )
                steps_status .append (f"<:lumen_dnd:1324983165554524252> {error_message }")
            finally :
                conn .close ()

        if not db_found or recovery_data is None :
            not_found_embed =discord .Embed (
            title ="Recovery Request Not Found",
            description =f"No recovery request found with ID `{recovery_id }` in any database.",
            color =0xff0000 
            )
            steps_status .append ("<:lumen_dnd:1324983165554524252> Recovery request not found in any database.")
            await message .edit (embed =not_found_embed )
            return 


        try :
            rejection_time =datetime .now (pytz .timezone ('Asia/Kolkata')).strftime ("%Y-%m-%d %H:%M:%S")
            channel_embed =discord .Embed (
            title ="Recovery Request Rejected",
            color =discord .Color .red (),
            timestamp =datetime .now (pytz .utc )
            )
            channel_embed .add_field (name ="Recovery ID",value =f"```{recovery_id }```",inline =False )
            channel_embed .add_field (name ="Previous User ID",value =f"```{previous_user_id }```",inline =True )
            channel_embed .add_field (name ="New User ID",value =f"```{new_user_id }```",inline =True )
            channel_embed .add_field (name ="Reason",value =f"```{reason }```",inline =False )
            channel_embed .add_field (name ="Rejected By",value =f"```{ctx .author } ({ctx .author .id })```",inline =False )
            channel_embed .add_field (name ="Rejection Time (Asia/Kolkata)",value =f"```{rejection_time }```",inline =False )


            channel =self .bot .get_channel (RECOVERY_REJECT_CHANNEL_ID )
            if channel is None :
                raise ValueError ("Recovery rejection channel not found. Please check the RECOVERY_REJECT_CHANNEL_ID.")

            await channel .send (embed =channel_embed )
            steps_status .append ("<:lumen_online:1326260453260656735> Rejection details sent to the recovery rejection channel.")
        except Exception as e :
            channel_error_embed =discord .Embed (
            title ="Channel Error",
            description =f"An error occurred while sending the rejection details to the channel: `{e }`",
            color =0xff0000 
            )
            logging .error (f"Error sending embed to channel: {e }")
            steps_status .append (f"<:lumen_dnd:1324983165554524252> Error sending embed to channel: `{e }`.")
            await message .edit (embed =channel_error_embed )
            return 


        dm_message =(
        f"Hello,\n\nYour recovery request with ID `{recovery_id }` has been **rejected**.\n\n"
        f"**Reason:** `{reason }`\n"
        f"**Rejected By:** {ctx .author } ({ctx .author .id })\n\n"
        f"If you have any further questions or believe this was a mistake, please contact support."
        )

        try :
            previous_user =await self .bot .fetch_user (int (previous_user_id ))
            dm_embed =discord .Embed (
            title ="Recovery Request Rejected",
            description =dm_message ,
            color =0xffb03b 
            )
            await previous_user .send (embed =dm_embed )
            steps_status .append ("<:lumen_online:1326260453260656735> DM sent to previous user.")
        except Exception as e :
            logging .warning (f"Could not DM previous user ({previous_user_id }): {e }")
            steps_status .append (f"<:lumen_dnd:1324983165554524252> Failed to DM previous user: `{e }`.")


        final_status ="\n".join (steps_status )
        final_embed =discord .Embed (
        title ="Recovery Request Rejected",
        description =f"Rejection of recovery request `{recovery_id }` has been processed.\n\n{final_status }",
        color =0x000001 
        )
        await message .edit (embed =final_embed )


async def setup (bot ):
    await bot .add_cog (RejectRecovery (bot ))
