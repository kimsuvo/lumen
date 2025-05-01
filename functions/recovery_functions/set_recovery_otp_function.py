

import os 
import sqlite3 
import random 
import smtplib ,ssl 
import glob 
import bcrypt 
from email .mime .text import MIMEText 
from email .mime .multipart import MIMEMultipart 


SENDER_ACCOUNTS =[
{"email":"lumenbot1@gmail.com","password":"morm ucax hnrt jhug"},
{"email":"lumenbot3@gmail.com","password":"nxiq hdhe uiig ffmg"},
{"email":"lumenbot4@gmail.com","password":"phlp nebh pgam lqcl"},
]

def send_otp_email (recipient_email ,otp ):
    """
    Sends an email containing the OTP to the recipient using one of the sender accounts.
    """

    sender =random .choice (SENDER_ACCOUNTS )
    sender_email =sender ["email"]
    sender_password =sender ["password"]


    message =MIMEMultipart ("alternative")
    message ["Subject"]="Your OTP Code"
    message ["From"]=sender_email 
    message ["To"]=recipient_email 


    text =f"Your OTP code is: {otp }"


    html =f"""
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
                margin: 20px 0;
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
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #777;
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
            <p>
                Please enter this code within the next 5 minutes. If you did not request this code, 
                please ignore this email or contact our support team.
            </p>
            <p>
                Thank you for trusting us to keep your account secure.
            </p>
            <hr/>
            <h3>About Lumen</h3>
            <p>
                Lumen is your trusted solution for seamless and secure feedback management. We pride ourselves on delivering 
                top-of-the-line security and reliability for all your feedbacks and reputation. 
                Join our community on our <a href="https://discord.gg/lumenbot" target="_blank">Discord server</a> to stay updated 
                and collaborate with other users.
            </p>
            <p>
                For more detailed information, please visit our Discord server or reach out to our support team at any time.
            </p>
            <footer class="footer">
                &copy; 2025 Lumen. All rights reserved.
            </footer>
        </div>
    </body>
    </html>
    """


    part1 =MIMEText (text ,"plain")
    part2 =MIMEText (html ,"html")
    message .attach (part1 )
    message .attach (part2 )


    context =ssl .create_default_context ()
    with smtplib .SMTP_SSL ("smtp.gmail.com",465 ,context =context )as server :
        server .login (sender_email ,sender_password )
        server .sendmail (sender_email ,recipient_email ,message .as_string ())


def find_user_database (user_id ,db_directory ="credentialsdatabase"):
    """
    Searches through all SQLite databases in the specified directory to find
    the one that contains the given user_id in the 'users' table.

    Returns the path to the database if found, else None.
    """
    if not os .path .exists (db_directory ):
        return None 

    for filename in os .listdir (db_directory ):
        if filename .endswith (".db"):
            db_path =os .path .join (db_directory ,filename )
            try :
                conn =sqlite3 .connect (db_path )
                cursor =conn .cursor ()
                cursor .execute ("SELECT user_id FROM users WHERE user_id = ?",(user_id ,))
                if cursor .fetchone ():
                    conn .close ()
                    return db_path 
                conn .close ()
            except sqlite3 .Error :
                continue 
    return None 


def is_user_premium (user_id :int )->bool :
    premium_db_dir ="premiumdatabase"
    db_files =sorted (glob .glob (os .path .join (premium_db_dir ,"*.db")))
    for db_file in db_files :
        try :
            conn =sqlite3 .connect (db_file )
            cursor =conn .cursor ()

            cursor .execute ("SELECT 1 FROM premium WHERE user_id = ?",(str (user_id ),))
            result =cursor .fetchone ()
            conn .close ()
            if result :
                return True 
        except sqlite3 .Error as e :
            print (f"Database error in {db_file }: {e }")
    return False 
