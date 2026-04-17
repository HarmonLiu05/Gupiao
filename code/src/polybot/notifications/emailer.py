import smtplib
from email.message import EmailMessage
from typing import TypeAlias

from pydantic import BaseModel

EmailAttachment: TypeAlias = tuple[str, bytes, str]


class SmtpEmailConfig(BaseModel):
    host: str = "smtp.qq.com"
    port: int = 465
    username: str
    auth_code: str
    to_address: str
    from_name: str = "US Stock Daily Report"


def send_email(
    config: SmtpEmailConfig,
    subject: str,
    body: str,
    attachments: list[EmailAttachment] | None = None,
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{config.from_name} <{config.username}>"
    message["To"] = config.to_address
    message.set_content(body, charset="utf-8")
    for filename, content, content_type in attachments or []:
        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=filename,
        )

    with smtplib.SMTP_SSL(config.host, config.port) as smtp:
        smtp.login(config.username, config.auth_code)
        smtp.send_message(message)
