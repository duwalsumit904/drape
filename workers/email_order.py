"""
Author: Sumit
Created: 5/13/2026
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def build_order_email(to: str, order_id: str, total: float, item_count: int) -> MIMEMultipart:
    """Build the order confirmation email HTML."""

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2>Order Confirmed ✅</h2>
        <p>Thank you for your order! Here's your summary:</p>
        <table style="width:100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Order ID</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{order_id}</b></td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Items</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{item_count}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Total</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>${total:.2f}</b></td>
          </tr>
        </table>
        <p style="margin-top: 20px; color: #888;">
          If you have any questions, reply to this email.
        </p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Order Confirmed -#{order_id[:8].upper()}"
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html,"html"))

    return msg

def send_order_confirmation(
        to: str,
        order_id: str,
        total: str,
        item_count: int
) -> None:

    """
     Blocking SMTP send. Called from the email worker.
    Raises on failure so RabbitMQ can requeue the message.

    """

    msg = build_order_email(to,order_id,total,item_count)


    try:
        with smtplib.SMTP(settings.MAIL_SERVER,settings.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.MAIL_USERNAME,settings.MAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Order confirmation sent → {to} (order: {order_id})")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP failed for order {order_id}: {e}")
        raise
