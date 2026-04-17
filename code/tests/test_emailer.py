from polybot.notifications.emailer import SmtpEmailConfig, send_email


class FakeSMTP:
    sent_messages = []

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, user, password):
        self.user = user
        self.password = password

    def send_message(self, message):
        self.sent_messages.append(message)


def test_send_email_uses_smtp_ssl(monkeypatch):
    monkeypatch.setattr("polybot.notifications.emailer.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.sent_messages.clear()

    config = SmtpEmailConfig(
        host="smtp.qq.com",
        port=465,
        username="sender@qq.com",
        auth_code="auth-code",
        to_address="receiver@example.com",
    )

    send_email(config, subject="hello", body="body")

    assert len(FakeSMTP.sent_messages) == 1
    assert FakeSMTP.sent_messages[0]["Subject"] == "hello"
