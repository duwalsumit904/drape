from workers.celery_app import celery_app
from app.core.config import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


@celery_app.task(
    # name="send_welcome_email",
    max_retries=3,
    default_retry_delay=60
)

def send_welcome_email(email: str,full_name:str):
    try:
        #create email

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to Drape!"
        msg["From"] = settings.MAIL_FROM
        msg["To"] = email

        #email body

        html = f"""

        <html>
            <body>
            <h1>
            Welcome to drape, {full_name}
                </h1>
                
                <p>Thank you for joining us</p>
                <p> Start shopping now </p>
            </body>
            </html>
            """
        msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP(settings.MAIL_SERVER,settings.MAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME,settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_FROM,email,msg.as_string())
        print(f"welcome email send to {email}")
        return {"status":"sent","email":email}

    except Exception as e:
        print(f"email failed :{e}")
        raise send_welcome_email.retry(exc=e)



@celery_app.task(
    name="send_otp_email",
    max_retries=3,
    default_retry_delay=60
)
def send_otp_email(email: str, otp: str, full_name: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Drape OTP Code"
        msg["From"]    = settings.MAIL_FROM
        msg["To"]      = email

        html = f"""
        <html>
            <body>
                <h2>Hello {full_name}!</h2>
                <p>Your OTP for password change:</p>
                <h1 style="color: #7c3aed; 
                           letter-spacing: 5px;">
                    {otp}
                </h1>
                <p>Valid for <b>5 minutes only.</b></p>
                <p>If you didn't request this, 
                   ignore this email.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(
            settings.MAIL_SERVER,
            settings.MAIL_PORT
        ) as server:
            server.starttls()
            server.login(
                settings.MAIL_USERNAME,
                settings.MAIL_PASSWORD
            )
            server.sendmail(
                settings.MAIL_FROM,
                email,
                msg.as_string()
            )
        return {"status": "sent", "email": email}

    except Exception as e:
        raise send_otp_email.retry(exc=e)
