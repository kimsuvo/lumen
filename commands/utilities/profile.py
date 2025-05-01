

import discord 
from discord .ext import commands 
import sqlite3 
from datetime import datetime 
import pytz 
import os 
import re 


from functions .profile_functions .userprofile_functions import (
get_custom_button ,
normalize_store_url ,
get_store_button_status ,
user_exists_in_ban_db ,
load_credentials ,
init_db ,
load_services_and_products ,
get_user_badges ,
init_imagethumbnail_tables ,
ensure_user_exists ,
update_image_data ,
get_user_data ,
get_feedback_counts ,
parse_and_normalize ,
get_latest_feedbacks ,
get_registration_date ,
get_services_and_products ,
get_image_data ,
get_user_color ,
get_user_status ,
get_verified_tick 
)
from functions .register_functions .registration_functions import RegisterModal ,RegisterButton ,ShowKeyButton 


init_db ()
init_imagethumbnail_tables ()







class PrevButton (discord .ui .Button ):
    def __init__ (self ):
        super ().__init__ (label ="",emoji =discord .PartialEmoji .from_str ("<:lumen_prev:1341817378786381835>"),style =discord .ButtonStyle .primary ,row =0 )

    async def callback (self ,interaction :discord .Interaction ):

        if interaction .user .id !=self .view .authorized_user .id :
            await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
            return 

        view :ProfileNavigationView =self .view 
        view .current_page =(view .current_page -1 )%len (view .pages )
        view .update_buttons ()
        try :
            await interaction .response .edit_message (embed =view .pages [view .current_page ],view =view )
        except discord .NotFound :
            pass 


class NextButton (discord .ui .Button ):
    def __init__ (self ):
        super ().__init__ (label ="",emoji =discord .PartialEmoji .from_str ("<:lumen_next:1341817363745476699>"),style =discord .ButtonStyle .primary ,row =0 )

    async def callback (self ,interaction :discord .Interaction ):

        if interaction .user .id !=self .view .authorized_user .id :
            await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
            return 

        view :ProfileNavigationView =self .view 
        view .current_page =(view .current_page +1 )%len (view .pages )
        view .update_buttons ()
        try :
            await interaction .response .edit_message (embed =view .pages [view .current_page ],view =view )
        except discord .NotFound :
            pass 






class ProfileNavigationView (discord .ui .View ):
    def __init__ (self ,pages ,store_button =None ,custom_button =None ,authorized_user =None ,timeout =60 ):
        super ().__init__ (timeout =timeout )
        self .pages =pages 
        self .current_page =0 
        self .authorized_user =authorized_user 



        self .prev_button =PrevButton ()
        self .next_button =NextButton ()
        self .add_item (self .prev_button )
        self .add_item (self .next_button )


        if store_button :
            self .add_item (store_button )
        if custom_button :
            self .add_item (custom_button )

        self .update_buttons ()


    def update_buttons (self ):

        pass 





class PreProfileCog (commands .Cog ,name ="Home - Lumen Profile"):
    def __init__ (self ,bot ):
        self .bot =bot 

    def create_profile_embed (
    self ,
    user ,
    registration_date ,
    badge_count ,
    positive_feedback_count ,
    negative_feedback_count ,
    total_feedback_count ,
    recent_feedbacks ,
    store ,
    products ,
    global_rank ,
    status 
    ):
        thumbnail_url ,image_url =get_image_data (user .id )
        tick =get_verified_tick (user .id )
        embed =discord .Embed (
        title ="Lumen Profile",
        description =f"## {user .display_name } {tick }",
        color =get_user_color (user .id )
        )
        embed .add_field (
        name ="Feedbacks Information",
        value =(f"Positive: {positive_feedback_count }\n"
        f"Negative: {negative_feedback_count }\n"
        f"Overall: {total_feedback_count }"),
        inline =True 
        )
        if badge_count :
            embed .add_field (name ="Badges",value =badge_count ,inline =False )
        else :
            embed .add_field (name ="Badges",value ="-# No badges assigned.",inline =False )

        embed .add_field (
        name ="Status",
        value =status if status else "-# No status set yet.",
        inline =False 
        )





        embed .add_field (
        name ="Services and Products",
        value =f"Store: {store }\nProducts:\n"+("\n".join (products )if products else "-# No products registered."),
        inline =False 
        )
        embed .set_thumbnail (url =thumbnail_url )
        embed .set_image (url =image_url )
        embed .set_footer (text ="Lumen | discord.gg/LumenBot")
        return embed 

    @commands .command (name ="profile",aliases =["p","P","Profile"])
    async def profile_prefix (self ,ctx ,user :discord .User =None ):
        if user is None :
            user =ctx .author 

        registration_date =get_registration_date (user .id )
        badge_count =get_user_badges (user .id )
        positive_feedback_count ,negative_feedback_count ,total_feedback_count ,global_rank =get_feedback_counts (user .id )
        store ,products =get_services_and_products (user .id )
        recent_feedbacks =get_latest_feedbacks (user .id )
        status =get_user_status (user .id )
        is_registered =not registration_date .startswith ("[Click the button below")


        thumbnail_url ,image_url =get_image_data (user .id )
        tick =get_verified_tick (user .id )





        home_embed =self .create_profile_embed (
        user ,
        registration_date ,
        badge_count ,
        positive_feedback_count ,
        negative_feedback_count ,
        total_feedback_count ,
        recent_feedbacks =recent_feedbacks ,
        store =store ,
        products =products ,
        global_rank =global_rank ,
        status =status 
        )
        home_embed .title ="Home - Lumen Profile"


        if not recent_feedbacks :
            feedback_desc ="-# No feedbacks received yet."
        else :
            feedback_desc ="\n".join (f"- {feedback [1 ]}"for feedback in recent_feedbacks )
        recent_embed =discord .Embed (
        title ="**Recent Feedbacks - Lumen Profile**",
        description =feedback_desc ,
        color =get_user_color (user .id )
        )
        recent_embed .set_footer (text ="Lumen | discord.gg/LumenBot")


        user_info_embed =discord .Embed (
        title ="**User Information - Lumen Profile**",
        description =f"{user .display_name } {tick }",
        color =get_user_color (user .id )
        )
        user_info_embed .add_field (name ="User ID",value =str (user .id ),inline =True )
        user_info_embed .add_field (name ="Registration Date",value =registration_date ,inline =True )
        user_info_embed .add_field (
        name ="Global Rank",
        value =f"Rank: {global_rank }",
        inline =False 
        )
        user_info_embed .set_thumbnail (url =thumbnail_url )
        user_info_embed .set_footer (text ="Lumen | discord.gg/LumenBot")

        pages =[home_embed ,recent_embed ,user_info_embed ]




        store_button =None 
        normalized_store =normalize_store_url (store )
        if get_store_button_status (user .id )and normalized_store .startswith ("http"):
            store_button =discord .ui .Button (
            label ="Visit Store",
            url =normalized_store ,
            style =discord .ButtonStyle .link ,
            row =0 
            )

        custom_ui_button =None 
        custom_button_data =get_custom_button (user .id )
        if custom_button_data :
            button_name ,url =custom_button_data 

            if not button_name .strip ():
                button_name ="Custom"
            custom_ui_button =discord .ui .Button (
            label =button_name ,
            url =url ,
            style =discord .ButtonStyle .link ,
            row =0 
            )





        view =ProfileNavigationView (pages ,store_button =store_button ,custom_button =custom_ui_button ,authorized_user =ctx .author ,timeout =60 )


        if (user .id ==ctx .author .id )and (not is_registered ):
            view .add_item (RegisterButton (authorized_user =user ))

        profile_message =await ctx .send (embed =pages [0 ],view =view )
        await profile_message .delete (delay =20 )

async def setup (bot ):
    await bot .add_cog (PreProfileCog (bot ))
