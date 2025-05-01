

import os 
import sqlite3 
import random 
import smtplib 
from email .mime .text import MIMEText 
from email .mime .multipart import MIMEMultipart 
import bcrypt 

def verify_email (email :str ,db_dir :str ="credentialsdatabase")->bool :
    """
    Checks if the given email (in plain text) is present in any of the database files
    in the specified directory. (The recovery_email is stored hashed, so we compare
    using bcrypt.)
    """
    if not os .path .isdir (db_dir ):
        print (f"Database directory '{db_dir }' not found.")
        return False 

    db_files =[f for f in os .listdir (db_dir )if f .endswith ('.db')]
    email_bytes =email .encode ('utf-8')

    for db_file in db_files :
        db_path =os .path .join (db_dir ,db_file )
        try :
            conn =sqlite3 .connect (db_path )
            cursor =conn .cursor ()
            cursor .execute ("SELECT recovery_email FROM users")
            rows =cursor .fetchall ()
            conn .close ()

            for row in rows :
                hashed_recovery_email =row [0 ]
                if hashed_recovery_email and bcrypt .checkpw (email_bytes ,hashed_recovery_email .encode ('utf-8')):
                    return True 
        except Exception as e :
            print (f"Error accessing {db_path }: {e }")
            continue 

    return False 

def send_otp_to_email (email :str ,email_accounts :list )->str :
    """
    Generates a 6-digit OTP, sends it via email using one of the provided email accounts,
    and returns the OTP.
    """
    otp =''.join (str (random .randint (0 ,9 ))for _ in range (6 ))
    email_account =random .choice (email_accounts )
    sender_email =email_account ["email"]
    sender_password =email_account ["password"]

    msg =MIMEMultipart ()
    msg ['From']=sender_email 
    msg ['To']=email 
    msg ['Subject']="Your OTP Code"

    body =f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <style type="text/css">
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #f4f4f4;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            padding: 40px;
            text-align: center;
            position: relative;
        }}
        .banner {{
            width: 100%;
            max-height: 200px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            object-fit: cover;
        }}
        .logo {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            border: 4px solid #fff;
            position: absolute;
            top: 150px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
        }}
        h2 {{
            margin-top: 70px;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .otp-code {{
            font-size: 36px;
            font-weight: bold;
            color: #d9534f;
            background-color: #f9f9f9;
            padding: 15px 25px;
            border-radius: 5px;
            margin-bottom: 20px;
            letter-spacing: 2px;
            display: inline-block;
        }}
        p {{
            font-size: 16px;
            line-height: 1.5;
        }}
        a {{
            color: #0275d8;
            text-decoration: none;
        }}
        hr {{
            margin: 30px 0;
            border: none;
            border-top: 1px solid #eee;
        }}
        @media (max-width: 600px) {{
            .container {{
                padding: 20px;
                margin: 20px;
            }}
            h2 {{
                font-size: 20px;
                margin-top: 60px;
            }}
            .otp-code {{
                font-size: 28px;
                padding: 10px 20px;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                top: 130px;
            }}
        }}
        </style>
    </head>
    <body>
        <div class="container">
        <img src="https://media.discordapp.net/attachments/1200750312844165203/1335544848266301520/lumenpremiumbanner.png?ex=67a08e91&is=679f3d11&hm=a83ae81ff8f34d2c33fd32246f42fa9251e07f0b1955b7fdd19eec7968ef124f&=&format=webp&quality=lossless&width=611&height=215" 
             alt="Lumen Banner" class="banner" />
        <img src="https://media.discordapp.net/attachments/1200750312844165203/1335544847796408410/lumenpremium.png?ex=67a08e90&is=679f3d10&hm=f011cd3b30ec3e6ebcc588cfae48432a70987b3cb40146046d817e8391abd43e&=&format=webp&quality=lossless&width=670&height=670" 
             alt="Lumen Logo" class="logo" />
        <h2>Your OTP Code</h2>
        <p class="otp-code">{otp }</p>
        <p>Please enter this code within the next 5 minutes. If you did not request this code, ignore this email or contact support.</p>
        <hr/>
        <h3>About Lumen</h3>
        <p>Lumen is your trusted solution for seamless and secure feedback management. 
           Join our community on our <a href="https://discord.gg/lumenbot" target="_blank">Discord server</a>.</p>
        <footer style="margin-top: 30px; font-size: 12px; color: #777;">
            <p>&copy; 2025 Lumen. All rights reserved.</p>
        </footer>
        </div>
    </body>
    </html>
    """
    msg .attach (MIMEText (body ,'html'))

    with smtplib .SMTP ('smtp.gmail.com',587 )as server :
        server .starttls ()
        try :
            server .login (sender_email ,sender_password )
        except smtplib .SMTPAuthenticationError :
            print ("Failed to authenticate with the SMTP server.")

            return otp 

        server .sendmail (sender_email ,email ,msg .as_string ())

    return otp 

def update_password (user_id :str ,new_password :str ,db_dir :str ="credentialsdatabase")->dict :
    """
    Updates the password for the user with the given user_id across all database files.
    The new password must be different from the current one.
    Returns the updated user record as a dictionary on success,
    or a dict with an "error" key on failure.
    """
    try :
        if not os .path .isdir (db_dir ):
            print (f"Database directory '{db_dir }' not found.")
            return {"error":"Internal server error. Please try again later."}

        db_files =[f for f in os .listdir (db_dir )if f .endswith ('.db')]

        for db_file in db_files :
            db_path =os .path .join (db_dir ,db_file )
            try :
                conn =sqlite3 .connect (db_path )
                conn .row_factory =sqlite3 .Row 
                cursor =conn .cursor ()


                cursor .execute ("SELECT user_id, password FROM users WHERE user_id = ?",(user_id ,))
                row =cursor .fetchone ()
                if row is None :
                    conn .close ()
                    continue 

                stored_password_hash =row ["password"]


                if bcrypt .checkpw (new_password .encode ('utf-8'),stored_password_hash .encode ('utf-8')):
                    conn .close ()
                    return {"error":"New password cannot be the same as the old password."}


                new_pw_hash =bcrypt .hashpw (new_password .encode ('utf-8'),bcrypt .gensalt ()).decode ('utf-8')
                cursor .execute ("UPDATE users SET password = ? WHERE user_id = ?",(new_pw_hash ,user_id ))
                conn .commit ()


                cursor .execute ("SELECT * FROM users WHERE user_id = ?",(user_id ,))
                updated_user =cursor .fetchone ()
                conn .close ()
                return dict (updated_user )

            except Exception as e :
                print (f"Error accessing {db_path }: {e }")
                continue 

        return {"error":"User not found. Please try again."}

    except Exception as e :
        print (f"Error in update_password: {e }")
        return {"error":"Internal server error. Please try again later."}
