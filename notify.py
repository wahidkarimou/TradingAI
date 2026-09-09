import os
import smtplib
from email.mime.text import MIMEText


def send_signal_email(result: dict):
    sender = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_APP_PASSWORD")
    recipient = os.environ.get("EMAIL_TO")

    if not sender or not password or not recipient:
        print("Notification email non configuree (variables d'environnement manquantes)")
        return

    subject = f"TradingAI — {result['symbol']} : {result['signal']}"
    body = f"""Nouveau signal TradingAI

Actif       : {result['symbol']}
Signal      : {result['signal']}
Prix        : {result['price']}
Stop Loss   : {result.get('sl')}
TP1         : {result.get('tp1')}
TP2         : {result.get('tp2')}
Confluence  : {result.get('confluence_score')}/100
Regime      : {result.get('regime')}
Invalidation: {result.get('invalidation')}

Dashboard : https://tradingai-cae6.onrender.com/?symbol={result['symbol']}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
        print("Email envoye avec succes")
    except Exception as e:
        print(f"Erreur envoi email: {e}")