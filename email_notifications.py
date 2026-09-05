import os
# import resend  <- This is removed
import sib_api_v3_sdk  # <-- This is added
from sib_api_v3_sdk.rest import ApiException # <-- This is added
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import base64

# Load environment variables from .env file
load_dotenv()

# --- Configure the Brevo API client --- (This section is changed)
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# This function is unchanged
def get_logo_attachment():
    try:
        with open("logo.png", "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return [{
                "filename": "logo.png",
                "content": encoded_string,
                "cid": "logo"
            }]
    except FileNotFoundError:
        print("Warning: logo.png not found. Emails will be sent without the logo.")
        return []

LOGO_ATTACHMENT = get_logo_attachment()


# --- Re-usable Email Sending Function --- (This function's logic is changed)
def send_email(params):
    """A centralized function to send emails using Brevo."""
    
    # Map your existing 'params' dictionary to the Brevo API format
    sender = {"email": params["from"]}
    to = [{"email": email} for email in params["to"]]
    
    # Handle CC if it exists
    cc = None
    if "cc" in params and params["cc"]:
        cc = [{"email": email} for email in params["cc"]]
        
    # Handle attachments for Brevo (especially for inline images)
    attachment = None
    if "attachments" in params and params["attachments"]:
        # This takes your logo and formats it for Brevo
        att = params["attachments"][0]
        attachment = [{
            "content": att["content"],
            "name": att["filename"],
            "content_id": att["cid"]  # This is crucial for cid:logo
        }]

    # Create the email object for Brevo
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        cc=cc,
        sender=sender,
        subject=params["subject"],
        html_content=params["html"],
        attachment=attachment
    )
    
    # Send the email using the Brevo API
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully! Message ID: {api_response.message_id}")
        return api_response.message_id
    except ApiException as e:
        print(f"Error sending email with Brevo: {e}")
        return None

# --- ALL YOUR OTHER FUNCTIONS REMAIN UNCHANGED ---

def send_assurance_approval_notification(email_receiver, product_name, price):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'✅ Assurance Approval Confirmed - {product_name} - PastPerfect ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)

def send_misc_listing_approval_request(price, name):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'⚠️ Approval Request: Miscellaneous Listing ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [ADMIN_EMAIL],
        "subject": subject,
        "html": html_body,
    }
    return send_email(params)
    
def send_misc_listing_approval(email_receiver, product_link, price):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'🎉 Miscellaneous Listing Approved! - PastPerfect ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)
    
def send_misc_rejection_notification(email_receiver, product_name, price, reason):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'❌ Miscellaneous Listing Rejected - {product_name} - PastPerfect ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)
    
def send_delivery_confirmation(email_receiver):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'📦 Order Delivered Successfully - PastPerfect ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)
    
def send_listing_confirmation(email_receiver, price, is_assured=False):
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'✅ Listing Confirmation - PastPerfect ({reference_id})'
    assurance_text = (
        "<p style='color: #004d40; font-weight: bold;'>We will contact you soon about assuring your product!</p>"
        if is_assured else ""
    )
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)
    
def ETA(order_date=None):
    today = datetime.today() if order_date is None else datetime.strptime(order_date, "%d-%m-%Y")
    days_until_sunday = (6 - today.weekday()) % 7
    delivery_date = today + timedelta(days=days_until_sunday)
    return delivery_date.strftime("%A, %d-%m-%Y")

def send_order_confirmation(email_receiver, product_name, price, order_date=None):
    delivery_date = ETA(order_date)
    reference_id = datetime.now().strftime("%H%M%S")
    subject = f'🎉 Order Confirmation - {product_name} for ₹{price} - PastPerfect ({reference_id})'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "cc": [ADMIN_EMAIL],
        "subject": subject,
        "html": html_body,
        "attachments": LOGO_ATTACHMENT,
    }
    return send_email(params)
    
def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_otp(email_receiver):
    otp = generate_otp()
    subject = 'Verify Your Email - PastPerfect'
    html_body = f"""...""" # Your HTML here
    params = {
        "from": SENDER_EMAIL,
        "to": [email_receiver],
        "subject": subject,
        "html": html_body,
    }
    send_email(params)
    return otp # Added return so your app can use the OTP
