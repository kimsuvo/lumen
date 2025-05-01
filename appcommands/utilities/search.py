import discord 
from discord import app_commands 
from discord .ext import commands 
import sqlite3 
import os 
import glob 
import re 
import io 
import nltk 
nltk .download ('wordnet')

try :
    from nltk .stem import PorterStemmer ,WordNetLemmatizer 
    from nltk .corpus import stopwords ,wordnet 
except ImportError :
    PorterStemmer =None 
    WordNetLemmatizer =None 
    stopwords =set ()
    wordnet =None 



try :
    from fuzzywuzzy import fuzz 
except ImportError :
    fuzz =None 

class AdvancedSearch :
    def __init__ (self ):

        self .filler_phrases =[
        "i need","i want","could you","can you","please",
        "search for","find","looking for","show me","give me"
        ]

        try :
            self .stopwords =set (stopwords .words ('english'))
        except LookupError :
            self .stopwords ={
            "a","an","the","is","are","of","in","on","at",
            "for","and","or","but","if","then","so","to","with",
            "by","from"
            }

        self .stemmer =PorterStemmer ()if PorterStemmer else None 
        self .lemmatizer =WordNetLemmatizer ()if WordNetLemmatizer else None 

    def extract_search_terms (self ,query :str )->list :
        """
        Process the query by:
          1. Lowercasing and removing filler phrases.
          2. Extracting quoted phrases for exact matching.
          3. Capturing boolean operators.
          4. Tokenizing (including wildcard tokens containing '*').
          5. Removing stopwords.
          6. Applying lemmatization and stemming.
          7. Returning a unique list of keywords.
        """
        query =query .lower ()
        for filler in self .filler_phrases :
            query =query .replace (filler ,"")
        query =query .strip ()


        quoted_phrases =re .findall (r'"(.*?)"',query )
        query =re .sub (r'"(.*?)"','',query )


        boolean_ops =re .findall (r'\b(and|or|not)\b',query )


        tokens =re .findall (r'\w+\*?\w*',query )
        tokens =[token for token in tokens if token and token not in self .stopwords ]


        processed_tokens =[]
        for token in tokens :
            if self .lemmatizer :
                try :
                    token =self .lemmatizer .lemmatize (token )
                except LookupError :

                    pass 
            if self .stemmer :
                token =self .stemmer .stem (token )
            processed_tokens .append (token )



        keywords =list (set (quoted_phrases +processed_tokens +boolean_ops ))
        return keywords 

    def expand_with_synonyms (self ,keywords :list )->list :
        """
        Expand each keyword with synonyms from WordNet.
        """
        expanded =set (keywords )
        if wordnet :
            for keyword in keywords :
                for syn in wordnet .synsets (keyword ):
                    for lemma in syn .lemma_names ():

                        expanded .add (lemma .lower ().replace ('_',' '))
        return list (expanded )

    def extract_range_filters (self ,query :str )->dict :
        """
        Extract range filters in the format: field:>value or field:<value.
        Returns a dictionary with field names as keys and tuples (operator, value).
        """
        filters ={}
        matches =re .findall (r'(\w+):([<>]=?\d+)',query )
        for field ,expression in matches :
            operator =expression [0 ]
            try :
                value =float (expression [1 :])
            except ValueError :
                value =None 
            filters [field ]=(operator ,value )
        return filters 

    def compute_relevance (self ,product_text :str ,keywords :list )->float :
        """
        Compute a relevance score for a product description by:
          - Counting exact phrase matches (weighted higher).
          - Counting single-word occurrences.
          - Using regex for wildcard tokens.
          - Optionally applying fuzzy matching if no exact match is found.
        """
        product_text_lower =product_text .lower ()
        relevance =0.0 


        tokens =re .findall (r'\w+',product_text_lower )
        if self .stemmer :
            tokens =[self .stemmer .stem (token )for token in tokens ]

        for keyword in keywords :
            if '*'in keyword :

                pattern =re .compile (keyword .replace ('*','.*'))
                matches =pattern .findall (product_text_lower )
                relevance +=len (matches )*2 
            elif " "in keyword :

                count =product_text_lower .count (keyword )
                relevance +=count *3 
            else :

                token_to_match =self .stemmer .stem (keyword )if self .stemmer else keyword 
                count =tokens .count (token_to_match )
                relevance +=count 

                if count ==0 and fuzz :
                    for token in tokens :
                        similarity =fuzz .ratio (token_to_match ,token )
                        if similarity >80 :
                            relevance +=similarity /100.0 
        return relevance 

    def format_products (self ,products :str )->str :
        """
        Sanitizes and formats the products string by stripping Discord markdown,
        custom emojis, and unnecessary symbols.
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

    def format_store_link (self ,store :str )->str :
        """
        Extracts and formats the store URL.
        If the store is given in Markdown format, extracts the URL.
        """
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
            url ="https://"+url 
        return f"[`Click here to visit store`]({url })"


class SearchProducts (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .searcher =AdvancedSearch ()

    async def get_username_from_id (self ,user_id ):
        """
        Fetches a Discord username based on the user ID.
        """
        try :
            user =await self .bot .fetch_user (user_id )
            return user .name if user else "Unknown"
        except discord .NotFound :
            return "Unknown"
        except discord .HTTPException :
            return "Error Fetching"

    @app_commands .command (name ="search",description ="Search for products using an advanced search algorithm")
    @app_commands .describe (query ="Your search query")
    async def search (self ,interaction :discord .Interaction ,query :str ):
        await interaction .response .defer ()


        keywords =self .searcher .extract_search_terms (query )
        if len (keywords )>4 :
            embed =discord .Embed (
            title ="Error",
            description ="You can only search with up to 4 keywords.",
            color =discord .Color .red ()
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 


        results =[]
        product_db_files =glob .glob (os .path .join ('productsdatabase','*.db'))
        for db_file in product_db_files :
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                like_clauses =" OR ".join (["products LIKE ?"]*len (keywords ))
                sql =f"SELECT user_id, store, products FROM services_and_products WHERE {like_clauses }"
                cursor .execute (sql ,tuple (f"%{kw }%"for kw in keywords ))
                results .extend (cursor .fetchall ())
            except sqlite3 .Error as e :
                print (f"Error fetching from {db_file }: {e }")
            finally :
                conn .close ()

        if not results :
            embed =discord .Embed (
            title ="No Results Found",
            description =f"No results found for {', '.join (keywords )}.",
            color =discord .Color .red ()
            )
            await interaction .followup .send (embed =embed )
            return 


        advanced_results =[]
        for res in results :
            user_id ,store ,products =res 
            relevance =self .searcher .compute_relevance (products ,keywords )
            if relevance >0 :
                advanced_results .append ((user_id ,store ,products ,relevance ))

        if not advanced_results :
            embed =discord .Embed (
            title ="No Relevant Results",
            description =f"No relevant results found for {', '.join (keywords )}.",
            color =discord .Color .red ()
            )
            await interaction .followup .send (embed =embed )
            return 


        user_feedback ={}
        feedback_db_files =glob .glob (os .path .join ('feedbackcountdatabase','*.db'))
        for db_file in feedback_db_files :
            try :
                conn =sqlite3 .connect (db_file )
                cursor =conn .cursor ()
                for res in advanced_results :
                    user_id =res [0 ]
                    try :
                        cursor .execute ("SELECT positive_feedback_count FROM feedback_count WHERE receiver_id = ?",(user_id ,))
                        data =cursor .fetchone ()
                        if data :
                            user_feedback [user_id ]=user_feedback .get (user_id ,0 )+data [0 ]
                    except sqlite3 .Error as e :
                        print (f"Error fetching feedback from {db_file }: {e }")
            except sqlite3 .Error as e :
                print (f"Error connecting to {db_file }: {e }")
            finally :
                conn .close ()


        sorted_results =sorted (
        advanced_results ,
        key =lambda x :(x [3 ],user_feedback .get (x [0 ],0 )),
        reverse =True 
        )


        display_results =sorted_results [:20 ]
        extended_results =sorted_results [:100 ]


        pages =[]
        page =[]
        for i ,res in enumerate (display_results ):
            user_id ,store ,products ,relevance =res 
            username =await self .get_username_from_id (user_id )
            rank =i +1 
            formatted_products =self .searcher .format_products (products )
            formatted_store =self .searcher .format_store_link (store )
            entry =(
            f"{rank }. **[{username }](https://discord.com/users/{user_id })**:\n"
            f"- {formatted_products }\n"
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
            title =f"Search Results for {', '.join (keywords )} ({len (sorted_results )} results found)",
            description ="\n\n".join (page ),
            color =0x000001 
            )
            embed .set_footer (text =f"Page {page_number } of {len (pages )}")
            embeds .append (embed )


        class PaginationView (discord .ui .View ):
            def __init__ (self ,interaction :discord .Interaction ,embeds :list ,extended_results :list ,cog_instance ,timeout :int =60 ):
                super ().__init__ (timeout =timeout )
                self .interaction =interaction 
                self .embeds =embeds 
                self .extended_results =extended_results 
                self .cog =cog_instance 
                self .current_page =0 
                self .update_buttons ()

            async def update_message (self ):
                self .update_buttons ()
                await self .interaction .edit_original_response (embed =self .embeds [self .current_page ],view =self )

            def update_buttons (self ):

                self .previous .disabled =self .current_page ==0 
                self .next .disabled =self .current_page ==len (self .embeds )-1 

            @discord .ui .button (label ="Previous",style =discord .ButtonStyle .primary )
            async def previous (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
                if interaction .user !=self .interaction .user :
                    await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
                    return 
                self .current_page =max (0 ,self .current_page -1 )
                await self .update_message ()
                await interaction .response .defer ()

            @discord .ui .button (label ="Next",style =discord .ButtonStyle .primary )
            async def next (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
                if interaction .user !=self .interaction .user :
                    await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
                    return 
                self .current_page =min (len (self .embeds )-1 ,self .current_page +1 )
                await self .update_message ()
                await interaction .response .defer ()

            @discord .ui .button (label ="Get TXT File for More",style =discord .ButtonStyle .secondary )
            async def get_txt (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
                if interaction .user !=self .interaction .user :
                    await interaction .response .send_message ("You cannot interact with these buttons.",ephemeral =True )
                    return 

                output =io .StringIO ()
                for idx ,res in enumerate (self .extended_results ):
                    user_id ,store ,products ,relevance =res 
                    formatted_products =self .cog .searcher .format_products (products )
                    output .write (f"{idx +1 }. {user_id }: {formatted_products }\n")
                output .seek (0 )
                file =discord .File (fp =io .BytesIO (output .getvalue ().encode ('utf-8')),filename ="extended_results.txt")


                dm_embed =discord .Embed (
                title ="Extended Search Results",
                description ="Here is your extended search results file.",
                color =0x000001 
                )

                try :
                    await interaction .user .send (embed =dm_embed ,file =file )
                    await interaction .response .send_message ("I've sent you a DM with the extended results.",ephemeral =True )
                except discord .Forbidden :
                    await interaction .response .send_message ("I cannot send you DMs. Please check your privacy settings.",ephemeral =True )






            async def on_timeout (self ):
                for child in self .children :
                    child .disabled =True 
                try :
                    await self .interaction .edit_original_response (view =self )
                except Exception as e :
                    print ("Error updating message on timeout:",e )

        view =PaginationView (interaction ,embeds ,extended_results ,self )
        await interaction .edit_original_response (embed =embeds [0 ],view =view )

    @commands .Cog .listener ()
    async def on_app_command_error (self ,interaction :discord .Interaction ,error :app_commands .AppCommandError ):

        if isinstance (error ,app_commands .CommandOnCooldown ):
            embed =discord .Embed (
            title ="Cooldown Active",
            description =f"You're on cooldown! Please try again in **{error .retry_after :.1f} seconds**.",
            color =discord .Color .red ()
            )
            try :
                await interaction .response .send_message (embed =embed ,ephemeral =True )
            except discord .InteractionResponded :
                await interaction .followup .send (embed =embed ,ephemeral =True )
        else :
            raise error 

async def setup (bot ):
    await bot .add_cog (SearchProducts (bot ))
