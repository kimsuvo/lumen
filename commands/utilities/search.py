import discord 
from discord .ext import commands 
from discord .ext .commands import BucketType 
import sqlite3 
import os 
import glob 
import re 

class PreSearchProducts (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .cooldown (rate =1 ,per =10 ,type =BucketType .user )
    @commands .command ()
    async def search (self ,ctx ,*,keyword :str ):

        initial_embed =discord .Embed (
        title ="**<a:lumen_loading:1326260453260656735> Searching...**",
        description ="Please wait while we search.",
        color =0x000001 
        )
        message =await ctx .send (embed =initial_embed )
        await ctx .defer ()


        keywords =[kw .strip ()for kw in keyword .split (",")]


        if len (keywords )>4 :
            error_embed =discord .Embed (
            title ="<:lumen_dnd:1324983165554524252> **Error**",
            description ="You can only search with up to 4 keywords.",
            color =discord .Color .red ()
            )
            await ctx .send (embed =error_embed )
            return 


        def format_products (products :str )->str :
            """
            This function:
            1. Splits the products text into lines.
            2. Removes extra Discord markdown formatting such as asterisks (*),
               underscores (_), backticks (`), tildes (~), and bullet dashes (-).
            3. If the lines are bullet‐listed:
               - If the bullets do not have an extra asterisk marker, the items are joined with commas.
               - If the first bullet starts with a dash and the following lines begin with an asterisk,
                 the first item is dropped and the remaining items are joined with a "  * " separator.
            4. Otherwise, the sanitized lines are simply joined with a space.
            """
            def sanitize_line (line :str )->str :





                line =re .sub (r'<a?:\w+:\d+>','',line )
                line =re .sub (r':[a-zA-Z0-9_]+:','',line )

                line =re .sub (r'[*_`~>|]','',line )


                emoji_pattern =re .compile ("["
                u"\U0001F600-\U0001F64F"
                u"\U0001F300-\U0001F5FF"
                u"\U0001F680-\U0001F6FF"
                u"\U0001F1E0-\U0001F1FF"
                "]+",flags =re .UNICODE )
                line =emoji_pattern .sub (r'',line )
                return line .strip ()




            raw_lines =[line for line in products .splitlines ()if line .strip ()]
            if not raw_lines :
                return ""


            bullet_list =any (line .lstrip ().startswith ("-")for line in raw_lines )

            if bullet_list :



                join_with_asterisk =any (
                line .lstrip ()[1 :].lstrip ().startswith ("*")
                for line in raw_lines if line .lstrip ().startswith ("-")
                )
                sanitized_lines =[]
                for line in raw_lines :
                    sline =line .strip ()
                    if sline .startswith ("-"):

                        sline =sline [1 :].strip ()
                    sanitized_lines .append (sanitize_line (sline ))
                if join_with_asterisk :

                    if len (sanitized_lines )>1 :
                        sanitized_lines =sanitized_lines [1 :]
                    if not sanitized_lines :
                        return ""
                    elif len (sanitized_lines )==1 :
                        return sanitized_lines [0 ]
                    else :

                        return sanitized_lines [0 ]+"  * "+" * ".join (sanitized_lines [1 :])
                else :


                    return ", ".join (sanitized_lines )
            else :

                sanitized_lines =[sanitize_line (line )for line in raw_lines ]
                return " ".join (sanitized_lines )


        def format_store_link (store :str )->str :
            store =store .strip ()if store else ""
            if not store :
                return "`No Store Link Provided`"
            url =store 


            if store .startswith ("[")and "("in store and ")"in store :
                start =store .find ('(')
                end =store .find (')',start )
                if start !=-1 and end !=-1 :
                    url =store [start +1 :end ].strip ()

            if not url .startswith ("http"):
                if url .startswith ("discord.gg"):
                    url ="https://"+url 
                else :
                    url ="https://"+url 
            return f"[`Click here to visit store`]({url })"


        results =[]
        product_db_files =glob .glob (os .path .join ('productsdatabase','*.db'))
        for db_file in product_db_files :
            try :
                product_conn =sqlite3 .connect (db_file )
                product_cursor =product_conn .cursor ()

                like_clauses =" OR ".join ([f"products LIKE ?"for _ in keywords ])
                query =f"""
                    SELECT user_id, store, products FROM services_and_products
                    WHERE {like_clauses }
                """
                product_cursor .execute (query ,tuple (f"%{kw }%"for kw in keywords ))
                results .extend (product_cursor .fetchall ())
            except sqlite3 .Error as e :
                print (f"Error fetching from {db_file }: {e }")
            finally :
                product_conn .close ()

        if not results :
            no_results_embed =discord .Embed (
            title ="<:lumen_dnd:1324983165554524252> **No Results Found**",
            description =f"No results found for {', '.join (keywords )}.",
            color =discord .Color .red ()
            )
            await message .edit (embed =no_results_embed )
            return 


        user_feedback ={}
        feedback_db_files =glob .glob (os .path .join ('feedbackcountdatabase','*.db'))
        for db_file in feedback_db_files :
            try :
                feedback_conn =sqlite3 .connect (db_file )
                feedback_cursor =feedback_conn .cursor ()
                for result in results :
                    user_id =result [0 ]
                    try :
                        feedback_cursor .execute (
                        "SELECT positive_feedback_count FROM feedback_count WHERE receiver_id = ?",
                        (user_id ,)
                        )
                        feedback_data =feedback_cursor .fetchone ()
                        if feedback_data :
                            user_feedback [user_id ]=user_feedback .get (user_id ,0 )+feedback_data [0 ]
                    except sqlite3 .Error as e :
                        print (f"Error fetching feedback from {db_file }: {e }")
            except sqlite3 .Error as e :
                print (f"Error connecting to {db_file }: {e }")
            finally :
                feedback_conn .close ()


        sorted_results =sorted (results ,key =lambda x :user_feedback .get (x [0 ],0 ),reverse =True )


        pages =[]
        page =[]
        for i ,result in enumerate (sorted_results ):
            user_id ,store ,products =result 

            username =await self .get_username_from_id (user_id )
            rank =i +1 

            formatted_products =format_products (products )
            formatted_store =format_store_link (store )


            entry =(
            f"{rank }. **[{username }](https://discord.com/users/{user_id })**:\n"
            f"-# {formatted_products }\n"
            f"{formatted_store }"
            )
            page .append (entry )
            if (i +1 )%5 ==0 :
                pages .append (page )
                page =[]
        if page :
            pages .append (page )


        embeds =[]
        for page_number ,page in enumerate (pages ,start =1 ):
            embed =discord .Embed (
            title =f"**Search Results for {', '.join (keywords )}** "
            f"({len (sorted_results )} results found)",
            description ="\n\n".join (page ),
            color =0x000001 
            )
            embed .set_footer (text =f"Page {page_number } of {len (pages )}")
            embeds .append (embed )


        class Pagination (discord .ui .View ):
            def __init__ (self ,ctx ,message ,embeds ,timeout =60 ):
                super ().__init__ (timeout =timeout )
                self .ctx =ctx 
                self .message =message 
                self .embeds =embeds 
                self .current_page =0 
                self .update_buttons ()

            async def update_message (self ):
                self .update_buttons ()
                await self .message .edit (embed =self .embeds [self .current_page ],view =self )

            def update_buttons (self ):
                self .previous .disabled =self .current_page ==0 
                self .next .disabled =self .current_page ==len (self .embeds )-1 

            @discord .ui .button (label ="Previous",style =discord .ButtonStyle .success )
            async def previous (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
                await interaction .response .defer ()
                if interaction .user !=self .ctx .author :
                    try :
                        await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
                    except discord .errors .InteractionResponded :
                        await interaction .followup .send ("You cannot interact with these buttons.",ephemeral =True )
                    return 
                if self .current_page >0 :
                    self .current_page -=1 
                    await self .update_message ()

            @discord .ui .button (label ="Next",style =discord .ButtonStyle .success )
            async def next (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
                await interaction .response .defer ()
                if interaction .user !=self .ctx .author :
                    try :
                        await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
                    except discord .errors .InteractionResponded :
                        await interaction .followup .send ("You cannot interact with these buttons.",ephemeral =True )
                    return 
                if self .current_page <len (self .embeds )-1 :
                    self .current_page +=1 
                    await self .update_message ()

            async def on_timeout (self ):
                for child in self .children :
                    child .disabled =True 
                await self .message .edit (view =self )

        view =Pagination (ctx ,message ,embeds )
        await message .edit (embed =embeds [0 ],view =view )


    async def get_username_from_id (self ,user_id ):
        try :
            user =await self .bot .fetch_user (user_id )
            return user .name if user else "Unknown"
        except discord .NotFound :
            return "Unknown"
        except discord .HTTPException :
            return "Error Fetching"

    @search .error 
    async def profile_prefix_error (self ,ctx ,error ):
        if isinstance (error ,commands .CommandOnCooldown ):
            cooldown_embed =discord .Embed (
            title ="**Cooldown Active**",
            description =f"You're on cooldown! Please try again in **{error .retry_after :.1f} seconds**.",
            color =0xff0000 ,
            timestamp =discord .utils .utcnow ()
            )
            cooldown_embed .set_footer (
            text =f"Requested by {ctx .author }",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            await ctx .send (embed =cooldown_embed ,delete_after =5 )
        else :
            raise error 

async def setup (bot ):
    await bot .add_cog (PreSearchProducts (bot ))
