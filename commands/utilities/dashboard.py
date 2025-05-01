import discord 
from discord .ext import commands 
import os 
import sqlite3 
from functions .profile_functions .userprofile_functions import get_user_badges 
from functions .profile_functions .userprofile_functions import get_feedback_counts 
from functions .premium_functions .premium_user_functions import is_user_premium 
from functions .dashboard_functions .profilesettings .status import fetch_dashboard_status 
from functions .dashboard_functions .profilesettings .store import fetch_dashboard_store 
from functions .dashboard_functions .profilesettings .products import fetch_dashboard_products 
from functions .dashboard_functions .profilesettings .storebutton import fetch_dashboard_storebutton 
from functions .image_functions .image import get_user_data 
from functions .dashboard_functions .custom_buttons_functions .custombutton import fetch_dashboard_custombutton ,remove_dashboard_custombutton 
from functions .dashboard_functions .profilesettings .storebutton import fetch_dashboard_storebutton ,update_dashboard_storebutton 
from functions .dashboard_functions .profilesettings .color import fetch_dashboard_color 
from functions .dashboard_functions .accounts .setrecovery import initiate_recovery_email_setup 
from functions .dashboard_functions .accounts .setrecovery import fetch_recovery_email 
from functions .premium_functions .premium_activate import user_has_premium 
from functions .dashboard_functions .accounts .premium import fetch_dashboard_premium 
from functions .blacklist .db_utils import find_user_blacklist_db 
from functions .dwc .db_utils import is_user_dwc 
from functions .register_functions .registration_functions import is_user_registered 
from functions .warnings .db_utils import DatabaseManager 
from functions .dashboard_functions .modals .store import StoreModal 
from functions .dashboard_functions .modals .products import ProductsModal 
from functions .dashboard_functions .modals .status import StatusModal 
from functions .dashboard_functions .modals .custombutton import CustomButtonModal 
from functions .dashboard_functions .modals .premium import PremiumModal 
from functions .topgg .vote import has_voted 
from config import DASHBOARD_PERMISSIONS_ID 


class DashboardEnterView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )

    @discord .ui .button (label ="Enter Dashboard",style =discord .ButtonStyle .success ,custom_id ="enter_dashboard")
    async def enter_dashboard (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

        if not is_user_registered (interaction .user .id ):
            error_embed =discord .Embed (
            title ="Registration Required",
            description ="You must register with Lumen before accessing the dashboard. Please register to continue.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =error_embed ,ephemeral =True )
            return 


        if not is_user_premium (interaction .user .id ):

            voted =await has_voted (interaction .user .id )
            if not voted :

                vote_embed =discord .Embed (
                title ="**Vote Required**",
                description ="You must vote for Lumen on [top.gg](https://top.gg/bot/1324057734009720915/vote) before entering the dashboard. Please vote using the button below.\n\n-# Consider upgrading to Lumen Premium to avoid limitations.",
                color =0x000001 
                )
                vote_button =discord .ui .Button (
                label ="Vote Lumen",
                style =discord .ButtonStyle .link ,
                url ="https://top.gg/bot/1324057734009720915/vote"
                )
                vote_view =discord .ui .View ()
                vote_view .add_item (vote_button )
                await interaction .response .send_message (embed =vote_embed ,view =vote_view ,ephemeral =True )
                return 


        dashboard_embed =discord .Embed (
        title ="Lumen Profile Dashboard",
        description ="Below are your current details.",
        color =0x000001 
        )
        dashboard_embed .add_field (name ="User ID:",value =f"-# {interaction .user .id }",inline =True )
        dashboard_embed .add_field (
        name ="Badges:",
        value =f"-# {get_user_badges (interaction .user .id )}",
        inline =True 
        )
        dashboard_embed .add_field (name ="User Mention:",value =f"-# {interaction .user .mention }",inline =False )

        positive ,negative ,total ,global_rank =get_feedback_counts (interaction .user .id )
        dashboard_embed .add_field (
        name ="Feedbacks Information:",
        value =f"-# Overall Feedbacks: {total }\n-# Positive Feedbacks: {positive }\n-# Negative Feedbacks: {negative }",
        inline =True 
        )

        premium_status =fetch_dashboard_premium (interaction .user .id )
        dashboard_embed .add_field (
        name ="Premium Information:",
        value =f"-# {premium_status }",
        inline =True 
        )
        dashboard_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67abcd14&is=67aa7b94&hm=29a1350ea1546643d815dc4e34a01922f2122af1dbd19e390e03a5643fff4ca6&=&format=webp&quality=lossless&width=670&height=670")
        dashboard_embed .set_footer (text ="Please select the dropdown for menu options below.")

        await interaction .response .send_message (embed =dashboard_embed ,view =DashboardSelectView (),ephemeral =True )




class DashboardSelectView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )
        self .add_item (DashboardSelect ())

class DashboardSelect (discord .ui .Select ):
    def __init__ (self ):
        options =[
        discord .SelectOption (label ="Profile Settings",description ="Manage your profile settings."),
        discord .SelectOption (label ="Account Settings",description ="Manage your account settings."),
        ]
        super ().__init__ (placeholder ="Select a menu option...",min_values =1 ,max_values =1 ,options =options )

    async def callback (self ,interaction :discord .Interaction ):
        selected =self .values [0 ]
        if selected =="Profile Settings":

            current_status =fetch_dashboard_status (interaction .user .id )
            current_store =fetch_dashboard_store (interaction .user .id )
            current_products =fetch_dashboard_products (interaction .user .id )
            current_storebutton =fetch_dashboard_storebutton (interaction .user .id )
            current_custombutton =fetch_dashboard_custombutton (interaction .user .id )
            current_color =fetch_dashboard_color (interaction .user .id )



            user_data =get_user_data (str (interaction .user .id ))
            current_banner =user_data .get ("image","")if user_data else ""
            current_banner_display =current_banner if current_banner and current_banner .strip ()!=""else "No banner set yet."


            user_data =get_user_data (str (interaction .user .id ))
            current_pfp =user_data .get ("thumbnail","")if user_data else ""
            current_pfp_display =current_pfp if current_pfp and current_pfp .strip ()!=""else "No pfp set yet."


            profile_embed =discord .Embed (
            title ="Profile Settings",
            description ="Your current profile information.",
            color =0x000001 
            )
            profile_embed .add_field (name ="Status:",value =f"{current_status }",inline =False )
            profile_embed .add_field (name ="Store:",value =f"-# {current_store }",inline =False )
            profile_embed .add_field (name ="Store Button:",value =f"-# {current_storebutton }",inline =False )
            profile_embed .add_field (name ="Products:",value =f"-# {current_products }",inline =False )
            profile_embed .add_field (name ="Custom Button:",value =f"-# {current_custombutton }",inline =False )
            profile_embed .add_field (name ="Color:",value =f"-# {current_color }",inline =False )
            profile_embed .add_field (name ="Banner:",value =f"-# {current_banner_display }",inline =False )
            profile_embed .add_field (name ="PFP:",value =f"-# {current_pfp_display }",inline =False )
            profile_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")


            await interaction .response .edit_message (
            embed =profile_embed ,
            view =ProfileSettingsView (
            user_id =interaction .user .id ,
            current_status =current_status ,
            current_store =current_store ,
            current_products =current_products ,
            current_storebutton =current_storebutton ,
            current_custombutton =current_custombutton ,
            current_color =current_color ,
            current_banner =current_banner_display ,
            current_pfp =current_pfp_display 
            )
            )



        elif selected =="Account Settings":
            recovery_status =fetch_recovery_email (interaction .user .id )
            premium_status =fetch_dashboard_premium (interaction .user .id )

            account_embed =discord .Embed (
            title ="Account Settings",
            description ="Your current account details.",
            color =0x000001 
            )
            account_embed .add_field (name ="Recovery Email:",value =f"-# {recovery_status }",inline =False )


            dwc_active =is_user_dwc (str (interaction .user .id ))
            dwc_status ="Active"if dwc_active else "Inactive"
            account_embed .add_field (name ="DWC Status:",value =f"-# {dwc_status }",inline =False )


            conn ,cursor =find_user_blacklist_db (str (interaction .user .id ))
            if conn and cursor :
                cursor .execute ("SELECT blacklist_status FROM blacklists WHERE user_id = ?",(str (interaction .user .id ),))
                result =cursor .fetchone ()
                blacklist_status =result [0 ]if result else "Not Blacklisted"
                conn .close ()
            else :
                blacklist_status ="Not Blacklisted"
            account_embed .add_field (name ="Blacklist Status:",value =f"-# {blacklist_status }",inline =False )


            warnings_manager =DatabaseManager (db_dir ="warningsdatabase",db_prefix ="warnings_")
            warnings_list =warnings_manager .get_warnings_for_user (str (interaction .user .id ))
            warnings_status =f"{len (warnings_list )} Warning(s)"if warnings_list else "No Warnings"
            account_embed .add_field (name ="Warnings:",value =f"-# {warnings_status }",inline =False )

            account_embed .add_field (name ="Premium Status:",value =f"-# {premium_status }",inline =False )
            account_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")


            await interaction .response .edit_message (embed =account_embed ,view =AccountSettingsView (recovery_email =recovery_status ,user_id =interaction .user .id ))



class ProfileSettingsView (discord .ui .View ):
    def __init__ (self ,user_id :int ,current_status :str =None ,current_store :str =None ,
    current_products :str =None ,current_storebutton :str =None ,
    current_custombutton :str =None ,current_color :str =None ,
    current_banner :str =None ,current_pfp :str =None ):
        super ().__init__ (timeout =None )

        for item in self .children :
            if isinstance (item ,discord .ui .Button ):
                if item .custom_id =="status_button":
                    if current_status in ["","none","-# No status set yet.",None ]:
                        item .label ="Set Status"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change Status"
                        item .style =discord .ButtonStyle .success 
                elif item .custom_id =="store_button":
                    if not current_store or current_store in ["Not Set","No set yet."]:
                        item .label ="Set Store"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change Store"
                        item .style =discord .ButtonStyle .success 
                elif item .custom_id =="products_button":
                    if not current_products or current_products =="No set yet.":
                        item .label ="Set Products"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change Products"
                        item .style =discord .ButtonStyle .success 
                elif item .custom_id =="storebutton_toggle":
                    if current_storebutton is None or current_storebutton =="Store Button OFF":
                        item .label ="Turn Store Button ON"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Turn Store Button OFF"
                        item .style =discord .ButtonStyle .danger 
                elif item .custom_id =="custom_button":
                    if not current_custombutton or current_custombutton =="No custom button set yet.":
                        item .label ="Set Custom Button"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Turn Custom Button OFF"
                        item .style =discord .ButtonStyle .danger 
                elif item .custom_id =="color_button":
                    if not current_color or current_color in ["No color set yet.","","none"]:
                        item .label ="Set Color"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change Color"
                        item .style =discord .ButtonStyle .success 
                elif item .custom_id =="banner_button":
                    if not current_banner or current_banner .lower ()in ["","none","no banner set yet."]:
                        item .label ="Set Banner"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change Banner"
                        item .style =discord .ButtonStyle .success 
                elif item .custom_id =="pfp_button":
                    if not current_pfp or current_pfp .strip ()==""or current_pfp .lower ()in ["no pfp set yet.","not set"]:
                        item .label ="Set PFP"
                        item .style =discord .ButtonStyle .primary 
                    else :
                        item .label ="Change PFP"
                        item .style =discord .ButtonStyle .success 


        from functions .premium_functions .premium_user_functions import is_user_premium 
        if not is_user_premium (user_id ):
            for item in self .children :
                if item .custom_id in ["pfp_button","storebutton_toggle","custom_button"]:
                    item .disabled =True 


    @discord .ui .button (label ="Set Status",style =discord .ButtonStyle .primary ,row =0 ,custom_id ="status_button")
    async def set_status (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_modal (StatusModal (interaction .user .id ))

    @discord .ui .button (label ="Set Store",style =discord .ButtonStyle .primary ,row =0 ,custom_id ="store_button")
    async def set_store (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_modal (StoreModal (interaction .user .id ))

    @discord .ui .button (label ="Toggle Store Button",style =discord .ButtonStyle .primary ,row =1 ,custom_id ="storebutton_toggle")
    async def toggle_storebutton (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        current_state_display =fetch_dashboard_storebutton (interaction .user .id )
        new_state ="no"if current_state_display =="Store Button ON"else "yes"
        update_dashboard_storebutton (interaction .user .id ,new_state )
        updated_storebutton =fetch_dashboard_storebutton (interaction .user .id )

        current_status =fetch_dashboard_status (interaction .user .id )
        current_store =fetch_dashboard_store (interaction .user .id )
        current_products =fetch_dashboard_products (interaction .user .id )
        updated_custombutton =fetch_dashboard_custombutton (interaction .user .id )
        current_color =fetch_dashboard_color (interaction .user .id )

        user_data =get_user_data (str (interaction .user .id ))
        current_banner =user_data .get ("image","")if user_data else ""
        current_banner_display =current_banner if current_banner and current_banner .strip ()!=""else "No banner set yet."

        user_data =get_user_data (str (interaction .user .id ))
        current_pfp =user_data .get ("thumbnail","")if user_data else ""
        current_pfp_display =current_pfp if current_pfp and current_pfp .strip ()!=""else "No pfp set yet."

        profile_embed =discord .Embed (
        title ="Profile Settings",
        description ="Your current profile information.",
        color =0x000001 
        )
        profile_embed .add_field (name ="Status:",value =f"{current_status }",inline =False )
        profile_embed .add_field (name ="Store:",value =f"-# {current_store }",inline =False )
        profile_embed .add_field (name ="Store Button:",value =f"-# {updated_storebutton }",inline =False )
        profile_embed .add_field (name ="Products:",value =f"-# {current_products }",inline =False )
        profile_embed .add_field (name ="Custom Button:",value =f"-# {updated_custombutton }",inline =False )
        profile_embed .add_field (name ="Color:",value =f"-# {current_color }",inline =False )
        profile_embed .add_field (name ="Banner:",value =f"-# {current_banner_display }",inline =False )
        profile_embed .add_field (name ="PFP:",value =f"-# {current_pfp_display }",inline =False )
        profile_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")

        new_view =ProfileSettingsView (
        user_id =interaction .user .id ,
        current_status =current_status ,
        current_store =current_store ,
        current_products =current_products ,
        current_storebutton =updated_storebutton ,
        current_custombutton =updated_custombutton ,
        current_color =current_color ,
        current_banner =current_banner_display ,
        current_pfp =current_pfp_display 
        )
        await interaction .response .edit_message (embed =profile_embed ,view =new_view )

    @discord .ui .button (label ="Set Products",style =discord .ButtonStyle .primary ,row =0 ,custom_id ="products_button")
    async def set_products (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_modal (ProductsModal (interaction .user .id ))

    @discord .ui .button (label ="Set Custom Button",style =discord .ButtonStyle .primary ,row =0 ,custom_id ="custom_button")
    async def set_custom_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        current_custombutton =fetch_dashboard_custombutton (interaction .user .id )
        if current_custombutton !="No custom button set yet.":
            remove_dashboard_custombutton (interaction .user .id )
            updated_custombutton =fetch_dashboard_custombutton (interaction .user .id )
            current_status =fetch_dashboard_status (interaction .user .id )
            current_store =fetch_dashboard_store (interaction .user .id )
            current_products =fetch_dashboard_products (interaction .user .id )
            current_storebutton =fetch_dashboard_storebutton (interaction .user .id )
            current_color =fetch_dashboard_color (interaction .user .id )

            user_data =get_user_data (str (interaction .user .id ))
            current_banner =user_data .get ("image","")if user_data else ""
            current_banner_display =current_banner if current_banner and current_banner .strip ()!=""else "No banner set yet."

            user_data =get_user_data (str (interaction .user .id ))
            current_pfp =user_data .get ("thumbnail","")if user_data else ""
            current_pfp_display =current_pfp if current_pfp and current_pfp .strip ()!=""else "No pfp set yet."

            profile_embed =discord .Embed (
            title ="Profile Settings",
            description ="Your current profile information.",
            color =0x000001 
            )
            profile_embed .add_field (name ="Status:",value =f"{current_status }",inline =False )
            profile_embed .add_field (name ="Store:",value =f"-# {current_store }",inline =False )
            profile_embed .add_field (name ="Store Button:",value =f"-# {current_storebutton }",inline =False )
            profile_embed .add_field (name ="Products:",value =f"-# {current_products }",inline =False )
            profile_embed .add_field (name ="Custom Button:",value =f"-# {updated_custombutton }",inline =False )
            profile_embed .add_field (name ="Color:",value =f"-# {current_color }",inline =False )
            profile_embed .add_field (name ="Banner:",value =f"-# {current_banner_display }",inline =False )
            profile_embed .add_field (name ="PFP:",value =f"-# {current_pfp_display }",inline =False )
            profile_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")

            new_view =ProfileSettingsView (
            user_id =interaction .user .id ,
            current_status =current_status ,
            current_store =current_store ,
            current_products =current_products ,
            current_storebutton =current_storebutton ,
            current_custombutton =updated_custombutton ,
            current_color =current_color ,
            current_banner =current_banner_display ,
            current_pfp =current_pfp_display 
            )
            await interaction .response .edit_message (embed =profile_embed ,view =new_view )
        else :
            await interaction .response .send_modal (CustomButtonModal (interaction .user .id ))

    @discord .ui .button (label ="Set Color",style =discord .ButtonStyle .primary ,row =1 ,custom_id ="color_button")
    async def set_color (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        from functions .dashboard_functions .modals .color import ColorModal 
        await interaction .response .send_modal (ColorModal (interaction .user .id ))

    @discord .ui .button (label ="Set Banner",style =discord .ButtonStyle .primary ,row =1 ,custom_id ="banner_button")
    async def set_banner (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        from functions .dashboard_functions .modals .banner import BannerModal 
        await interaction .response .send_modal (BannerModal (interaction .user .id ))

    @discord .ui .button (label ="Set PFP",style =discord .ButtonStyle .primary ,row =1 ,custom_id ="pfp_button")
    async def set_pfp (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        from functions .dashboard_functions .modals .pfp import PfpModal 
        await interaction .response .send_modal (PfpModal (interaction .user .id ))



class AccountSettingsView (discord .ui .View ):
    def __init__ (self ,recovery_email :str ,user_id :int ):
        super ().__init__ (timeout =None )
        for item in self .children :
            if isinstance (item ,discord .ui .Button ):
                if item .custom_id =="recovery_email_button":
                    if recovery_email =="No recovery email set yet.":
                        item .label ="Set Recovery Email"
                    else :
                        item .label ="Change Recovery Email"
                elif item .custom_id =="premium_button":
                    if user_has_premium (str (user_id )):
                        item .label ="Extend Premium"
                    else :
                        item .label ="Activate Premium"

        from functions .premium_functions .premium_user_functions import is_user_premium 
        if not is_user_premium (user_id ):
            for item in self .children :
                if item .custom_id =="recovery_email_button":
                    item .disabled =True 

        if recovery_email =="Recovery Email Set.":
            self .add_item (RemoveRecoveryEmailButton ())


    @discord .ui .button (label ="Set Recovery Email",style =discord .ButtonStyle .primary ,custom_id ="recovery_email_button")
    async def set_recovery_email (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        from functions .dashboard_functions .accounts .setrecovery import initiate_recovery_email_setup 
        await initiate_recovery_email_setup (interaction )

    @discord .ui .button (label ="Activate Premium",style =discord .ButtonStyle .primary ,custom_id ="premium_button")
    async def activate_premium (self ,interaction :discord .Interaction ,button :discord .ui .Button ):

        await interaction .response .send_modal (PremiumModal (interaction .user .id ))

    @discord .ui .button (label ="Change Password",style =discord .ButtonStyle .primary )
    async def change_password (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        from functions .dashboard_functions .accounts .changepassword import initiate_change_password 
        await initiate_change_password (interaction )



class RemoveRecoveryEmailButton (discord .ui .Button ):
    def __init__ (self ):
        super ().__init__ (label ="Remove Recovery Email",style =discord .ButtonStyle .danger ,custom_id ="remove_recovery_email_button")

    async def callback (self ,interaction :discord .Interaction ):
        from functions .dashboard_functions .accounts .recoverybuttonremove import initiate_remove_recovery_email 
        await initiate_remove_recovery_email (interaction )



class LumenDashboard (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="dashboard")
    async def dashboard (self ,ctx :commands .Context ):
        """
        Usage: +dashboard
        Sends an initial welcome embed with an 'Enter Dashboard' button.
        """
        if DASHBOARD_PERMISSIONS_ID not in [role .id for role in ctx .author .roles ]:
            return 


        welcome_embed =discord .Embed (
        title ="**Lumen Dashboard**",
        description =(
        "Welcome to **Lumen's** Dashboard, your gateway to managing your personal Lumen profile seamlessly.\n"
        "-# Click **Enter Dashboard** below to access your control panel.\n\n"
        "**Why Use This Dashboard?**\n"
        "-# **Profile Customization** – Update your status, banner, and profile picture with ease.\n"
        "-# **Account Management** – Securely manage your recovery email and premium settings.\n"
        "-# **Enhanced Experience** – Enjoy a tailored interface designed for your personal needs.\n\n"
        "**Note:** This dashboard is dedicated to personal profile management and does not include administrative controls."
        ),
        color =0x000001 

        )
        welcome_embed .set_footer (text ="Lumen Dashboard | Secure & Efficient",icon_url ="https://media.discordapp.net/attachments/1200750312844165203/1327572351432392704/lumencircle.png?ex=67abc359&is=67aa71d9&hm=94d9bf37ad65708eff64bf1d0af3d87884b8cd9eed786849445d663008b738d8&=&format=webp&quality=lossless&width=670&height=670")
        welcome_embed .set_thumbnail (url ="https://media.discordapp.net/attachments/1200750312844165203/1323958920691318784/Artboard_12x.png?ex=67ac75d4&is=67ab2454&hm=bc00f2abedf7e36cd93a33c1d2cf69defdd397022402602f90ffb5a14e82d5ea&=&format=webp&quality=lossless&width=670&height=670")
        await ctx .send (embed =welcome_embed ,view =DashboardEnterView ())



async def setup (bot :commands .Bot ):
    await bot .add_cog (LumenDashboard (bot ))

    bot .add_view (DashboardEnterView ())
