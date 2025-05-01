

import os 
import math 
from datetime import datetime 
import pandas as pd 
from fpdf import FPDF 
from PyPDF2 import PdfReader ,PdfWriter 


class WatermarkPDF (FPDF ):
    def rotate (self ,angle ,x =None ,y =None ):
        """
        Rotates the coordinate system by the given angle (in degrees).
        """
        if x is None :
            x =self .x 
        if y is None :
            y =self .y 
        angle_rad =math .radians (angle )
        c =math .cos (angle_rad )
        s =math .sin (angle_rad )
        cx =x *self .k 
        cy =(self .h -y )*self .k 
        self ._out (f'q {c :.3f} {s :.3f} {-s :.3f} {c :.3f} {cx -c *cx +s *cy :.3f} {cy -s *cx -c *cy :.3f} cm')

    def unrotate (self ):
        """Ends the rotation."""
        self ._out ('Q')

    def header (self ):
        """
        Override header() to draw a repeated (patterned) watermark
        in the background on each page.
        """

        try :
            self .set_alpha (0.30 )
        except Exception :
            pass 


        self .set_font ('Poppins','B',50 )

        self .set_text_color (200 ,200 ,200 )


        spacing =70 
        for x in range (-int (self .w ),int (self .w *2 ),spacing ):
            for y in range (-int (self .h ),int (self .h *2 ),spacing ):
                self .rotate (45 ,x ,y )
                self .text (x ,y ,"LUMEN")
                self .unrotate ()


        try :
            self .set_alpha (1 )
        except Exception :
            pass 

def create_password_protected_pdf (
df :pd .DataFrame ,
user_id :int ,
days :str ,
username :str ,
server_name :str ,
server_id :str 
)->tuple :
    """
    Create a password-protected PDF from a DataFrame of feedback records.
    The PDF is saved locally, then encrypted, and the unencrypted file is deleted.
    
    :param df: DataFrame containing feedback data
    :param user_id: The Discord user's ID
    :param days: Number of days requested or "all"
    :param username: The Discord user's name
    :param server_name: Name of the server where the command was used
    :param server_id: ID of the server where the command was used
    :return: Tuple (encrypted_file_name, password)
    """
    file_name =f"{user_id }_{days }_feedback.pdf"
    password =f"{user_id }{days }"


    pdf =WatermarkPDF ()
    pdf .set_auto_page_break (auto =True ,margin =15 )


    pdf .add_font ('Poppins','','fonts/poppins_regular.ttf',uni =True )
    pdf .add_font ('Poppins','B','fonts/poppins_bold.ttf',uni =True )


    pdf .add_page ()

    pdf .set_font ('Poppins','',5 )

    if days =="all":
        title_text ="LUMEN ALL FEEDBACKS"
    else :
        title_text =f"LUMEN LAST {days } DAY(S) FEEDBACKS"
    pdf .set_font ('Poppins','B',12 )
    pdf .cell (200 ,10 ,txt =title_text ,ln =True ,align ='C')
    pdf .ln (10 )

    pdf .set_font ('Poppins','B',5 )
    pdf .cell (200 ,8 ,txt =f"User ID: {user_id }",ln =True )
    pdf .cell (200 ,8 ,txt =f"Username: {username }",ln =True )
    pdf .cell (200 ,8 ,txt =f"Requested from Server: {server_name }",ln =True )
    pdf .cell (200 ,8 ,txt =f"Server ID: {server_id }",ln =True )

    total_feedbacks =len (df )
    pdf .cell (200 ,8 ,txt =f"Total Feedbacks Received in {days }: {total_feedbacks }",ln =True )
    pdf .cell (200 ,8 ,txt =f"Timestamp: {datetime .now ().strftime ('%Y-%m-%d %I:%M %p')}",ln =True )
    pdf .ln (10 )


    headers =['Giver ID','Feedback','Feedback Type','Timestamp']
    pdf .set_font ('Poppins','B',4 )
    column_widths =[37 ,65 ,37 ,56 ]
    for width ,header in zip (column_widths ,headers ):
        pdf .cell (width ,8 ,header ,border =1 ,align ='C')
    pdf .ln ()

    pdf .set_font ('Poppins','',4 )
    for _ ,row in df .iterrows ():
        pdf .cell (37 ,8 ,str (row ['Giver ID']),border =1 ,align ='C')
        pdf .cell (65 ,8 ,str (row ['Feedback']),border =1 ,align ='C')
        pdf .cell (37 ,8 ,str (row ['Feedback Type']),border =1 ,align ='C')
        pdf .cell (56 ,8 ,str (row ['Timestamp']),border =1 ,align ='C')
        pdf .ln ()
        if pdf .get_y ()>250 :
            pdf .add_page ()
            pdf .set_font ('Poppins','B',4 )
            for width ,header in zip (column_widths ,headers ):
                pdf .cell (width ,8 ,header ,border =1 ,align ='C')
            pdf .ln ()


    pdf .output (file_name )


    encrypted_file_name =f"{user_id }_{days }_feedback_encrypted.pdf"
    reader =PdfReader (file_name )
    writer =PdfWriter ()
    for page in reader .pages :
        writer .add_page (page )
    writer .encrypt (password )
    with open (encrypted_file_name ,'wb')as encrypted_file :
        writer .write (encrypted_file )


    if os .path .exists (file_name ):
        os .remove (file_name )

    return encrypted_file_name ,password 
