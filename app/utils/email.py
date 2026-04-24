from email.message import EmailMessage
import smtplib
from flask import current_app
from app.utils.helpers import format_datetime_sg
import json
import logging

logger = logging.getLogger(__name__)


def _build_smtp_client():
  host = current_app.config.get('MAIL_SERVER') or None
  username = current_app.config.get('MAIL_USERNAME') or None
  password = current_app.config.get('MAIL_PASSWORD') or None
  port = current_app.config.get('MAIL_PORT', 587)
  use_tls = current_app.config.get('MAIL_USE_TLS', True)

  if not host or not username or not password:
    logger.warning(f"Email config incomplete: host={bool(host)}, username={bool(username)}, password={bool(password)}")
    return None

  try:
    port = int(port)
    if not (1 <= port <= 65535):
      raise ValueError(f"Port {port} out of valid range 1-65535")
  except (ValueError, TypeError) as e:
    logger.warning(f"Invalid MAIL_PORT '{port}', falling back to 587: {e}")
    port = 587

  use_tls = bool(use_tls)

  try:
    client = smtplib.SMTP(host, port, timeout=10)
    if use_tls:
      client.starttls()
    client.login(username, password)
    return client
  except Exception as e:
    logger.error(f"SMTP connection failed: {str(e)}")
    return None


def send_email(to_address, subject, html_body, text_body=None):
  sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
  if not sender or not to_address:
    logger.warning(f"Email missing required fields: sender={bool(sender)}, to_address={bool(to_address)}")
    return False

  msg = EmailMessage()
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = to_address
  msg.set_content(text_body or '')
  msg.add_alternative(html_body, subtype='html')

  client = _build_smtp_client()
  if not client:
    logger.error(f"Failed to build SMTP client for email to {to_address}")
    return False

  try:
    client.send_message(msg)
    client.quit()
    logger.info(f"Email sent successfully to {to_address}: {subject}")
    return True
  except Exception as e:
    logger.error(f"Failed to send email to {to_address}: {str(e)}")
    try:
      client.quit()
    except Exception:
      pass
    return False


def send_welcome_email(user):
  subject = "Welcome to Looph"
  text_body = f"Hi {user.full_name or user.username}, welcome to Looph."
  html_body = f"""
  <h1>Welcome to Looph</h1>
  <p>Hi {user.full_name or user.username},</p>
  <p>Thanks for creating an account with Looph. You can now save your details for faster checkout and track your orders in your profile.</p>
  """
  return send_email(user.email, subject, html_body, text_body)


def _format_order_items(order):
  try:
    items = json.loads(order.items or '[]')
  except (TypeError, json.JSONDecodeError):
    items = []
  lines = []
  for item in items:
    name = item.get('product_name') or item.get('name') or 'Item'
    qty = int(item.get('quantity', 0))
    price = float(item.get('price', 0))
    lines.append(f"{name} x {qty} — ₱{price:.2f}")
  return items, "<br>".join(lines)


def send_order_receipt_email(order):
  items, items_html = _format_order_items(order)
  subject = f"Your Looph order #{order.id}"
  text_body = f"Thanks for your order #{order.id}. Total: ₱{order.total_amount:.2f}."
  html_body = f"""
  <h1>Order confirmation #{order.id}</h1>
  <p>Hi {order.customer_name},</p>
  <p>Thanks for shopping at Looph. Here is a summary of your order placed on {format_datetime_sg(order.created_at)}.</p>
  <h3>Items</h3>
  <p>{items_html}</p>
  <h3>Summary</h3>
  <p>Subtotal: ₱{order.subtotal:.2f}<br>
  Shipping: ₱{order.shipping_fee:.2f}<br>
  Total: ₱{order.total_amount:.2f}<br>
  Payment method: {order.payment_method.upper()}</p>
  """
  return send_email(order.customer_email, subject, html_body, text_body)


def send_order_status_email(order, old_status, new_status):
  subject = f"Update on your Looph order #{order.id}"
  text_body = f"Your order #{order.id} status changed from {old_status} to {new_status}."
  html_body = f"""
  <h1>Order update #{order.id}</h1>
  <p>Hi {order.customer_name},</p>
  <p>Your order status changed from <strong>{old_status}</strong> to <strong>{new_status}</strong>.</p>
  <p>Current status: {new_status}</p>
  """
  return send_email(order.customer_email, subject, html_body, text_body)

