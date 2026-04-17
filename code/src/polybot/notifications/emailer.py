import smtplib
from email.message import EmailMessage

from pydantic import BaseModel


class SmtpEmailConfig(BaseModel):
    host: str = "smtp.qq.com"
    port: int = 465
    username: str
    auth_code: str
    to_address: str
    from_name: str = "US Stock Daily Report"


def send_email(config: SmtpEmailConfig, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{config.from_name} <{config.username}>"
    message["To"] = config.to_address
    message.set_content(body, charset="utf-8")

    with smtplib.SMTP_SSL(config.host, config.port) as smtp:
        smtp.login(config.username, config.auth_code)
        smtp.send_message(message)
