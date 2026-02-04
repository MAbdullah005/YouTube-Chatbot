from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="your_email@gmail.com",
    MAIL_PASSWORD="your_app_password",
    MAIL_FROM="your_email@gmail.com",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,

    MAIL_STARTTLS=True,   # ✅ NEW
    MAIL_SSL_TLS=False,  # ✅ NEW

    USE_CREDENTIALS=True
)

async def send_verification_email(email: str, token: str):
    link = f"http://127.0.0.1:8000/auth/verify-email?token={token}"

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Click the link to verify your email:\n\n{link}",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
