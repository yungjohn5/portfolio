import os
import json
import urllib.request
import urllib.parse
import resend
from flask import Flask, request, send_from_directory, send_file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")

resend.api_key = os.environ["RESEND_API_KEY"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECAPTCHA_SECRET_KEY = os.environ["RECAPTCHA_SECRET_KEY"]


def verify_recaptcha(token):
    data = urllib.parse.urlencode({
        "secret": RECAPTCHA_SECRET_KEY,
        "response": token,
    }).encode()
    with urllib.request.urlopen("https://www.google.com/recaptcha/api/siteverify", data) as resp:
        result = json.loads(resp.read())
    return result.get("success", False)


@app.route("/")
def index():
    return send_from_directory(".", "index-grey.html")



@app.route("/resume/download")
def resume_download():
    return send_file("resume/Divine_amuzie.pdf",
                     as_attachment=True,
                     download_name="Divine_amuzie.pdf")


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()
    package = request.form.get("package", "").strip()

    recaptcha_token = request.form.get("g-recaptcha-response", "")

    if not all([name, email, phone, message]):
        return "missing_fields", 400

    # Validate email: must have @, a domain with a dot, and a TLD of ≥2 chars
    parts = email.split("@")
    if len(parts) != 2 or not parts[0] or "." not in parts[1] or len(parts[1].split(".")[-1]) < 2:
        return "invalid_email", 400

    try:
        captcha_ok = verify_recaptcha(recaptcha_token)
    except Exception:
        captcha_ok = False

    if not captcha_ok:
        return "captcha_failed", 400

    subject = f"Pricing Enquiry: {package}" if package else "New Contact Message"
    message_html = message.replace("\n", "<br>")

    try:
        resend.Emails.send({
            "from": f"Portfolio Contact <{SENDER_EMAIL}>",
            "to": RECIPIENT_EMAIL,
            "reply_to": email,
            "subject": subject,
            "html": (
                f"<p><strong>Name:</strong> {name}</p>"
                f"<p><strong>Email:</strong> {email}</p>"
                f"<p><strong>Phone:</strong> {phone}</p>"
                f"<p><strong>Message:</strong><br>{message_html}</p>"
            ),
        })
        return "sent"
    except Exception:
        return "send_failed", 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
