import discord 
from functions .image_functions .image import update_image_data ,get_user_data ,ensure_user_exists 
from functions .dashboard_functions .profilesettings .status import fetch_dashboard_status 
from functions .dashboard_functions .profilesettings .store import fetch_dashboard_store 
from functions .dashboard_functions .profilesettings .products import fetch_dashboard_products 
from functions .dashboard_functions .profilesettings .storebutton import fetch_dashboard_storebutton 
from functions .dashboard_functions .custom_buttons_functions .custombutton import fetch_dashboard_custombutton 
from functions .dashboard_functions .profilesettings .color import fetch_dashboard_color 

class BannerModal (discord .ui .Modal ,title ="Update Banner"):
    banner_input =discord .ui .TextInput (
    label ="Enter Banner URL:",
    style =discord .TextStyle .short ,
    required =False ,
    max_length =400 ,
    placeholder ="Type your banner URL here (max 400 characters)..."
    )

    def __init__ (self ,user_id :int ):
        super ().__init__ ()
        self .user_id =user_id 

    async def on_submit (self ,interaction :discord .Interaction ):
        new_banner =self .banner_input .value 
        user_id_str =str (self .user_id )


        ensure_user_exists (user_id_str ,"image",new_banner )
        update_image_data (user_id_str ,"image",new_banner )


        user_data =get_user_data (user_id_str )
        current_banner =user_data .get ("image","")if user_data else ""
        current_banner_display =current_banner if current_banner and current_banner .strip ()!=""else "No banner set yet."


        user_data =get_user_data (str (self .user_id ))
        current_pfp =user_data .get ("thumbnail","")if user_data else ""
        current_pfp_display =current_pfp if current_pfp and current_pfp .strip ()!=""else "No pfp set yet."


        current_status =fetch_dashboard_status (self .user_id )
        current_store =fetch_dashboard_store (self .user_id )
        current_products =fetch_dashboard_products (self .user_id )
        current_storebutton =fetch_dashboard_storebutton (self .user_id )
        current_custombutton =fetch_dashboard_custombutton (self .user_id )
        current_color =fetch_dashboard_color (self .user_id )

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



        from commands .utilities .dashboard import ProfileSettingsView 
        view =ProfileSettingsView (
        user_id =self .user_id ,
        current_status =current_status ,
        current_store =current_store ,
        current_products =current_products ,
        current_storebutton =current_storebutton ,
        current_custombutton =current_custombutton ,
        current_color =current_color ,
        current_banner =current_banner_display ,
        current_pfp =current_pfp_display 
        )

        await interaction .response .edit_message (embed =profile_embed ,view =view )
