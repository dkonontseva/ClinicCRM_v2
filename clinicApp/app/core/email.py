from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Clinic CRM"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='./templates/email'
)

fastmail = FastMail(conf)

async def send_email(subject: str, recipients: List[str], body: str):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype="html"
        )
        await fastmail.send_message(message)
        print(f"✅ Email sent successfully to {recipients}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise 