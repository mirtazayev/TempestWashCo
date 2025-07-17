# main.py

import base64
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import List

import aiosmtplib
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi import status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr, BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from services.invoice_func import generate_pdf

app = FastAPI(
    title="Tempest Wash Co Cleaning Services",
    description="Professional cleaning services for homes and businesses",
    version="1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="verymyrandomlongkey2025abc", max_age=10)
# Add global template variables
templates.env.globals["current_year"] = datetime.now().year


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    phone: str
    message: str


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "info@tempestwashco.com"
SMTP_PASS = "zsnu tnqj nkzj jwgt "
RECEIVER_EMAIL = "mirtazayev.2004@gmail.com"


def send_email(contact: ContactForm):
    msg = EmailMessage()
    msg['Subject'] = f"🚀 New Lead - Tempest Wash Co | {contact.phone}"
    msg['From'] = SMTP_USER
    msg['To'] = RECEIVER_EMAIL

    # Plain Text Body
    text_body = f"""
    You have received a new inquiry from your website contact form.

    Name: {contact.name}
    Email: {contact.email}
    Phone: {contact.phone}

    Message:
    {contact.message}
    """

    # HTML Body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: cadetblue;">📬 New Website Inquiry</h2>
        <p><strong>Name:</strong> {contact.name}</p>
        <p><strong>Email:</strong> <a href="mailto:{contact.email}">{contact.email}</a></p>
        <p><strong>Phone:</strong> <a href="tel:{contact.phone}">{contact.phone}</a></p>
        <p><strong>Message:</strong></p>
        <p style="background-color: #f4f4f4; padding: 10px; border-left: 4px solid cadetblue;">
            {contact.message}
        </p>
        <hr>
        <p style="font-size: 0.9em; color: #888;">Sent via tempestwashco.com contact form</p>
    </body>
    </html>
    """

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    # Confirmation email to customer (HTML + plain text fallback)
    user_msg = EmailMessage()
    user_msg['Subject'] = "We've received your request – Tempest Wash Co 🚿"
    user_msg['From'] = SMTP_USER
    user_msg['To'] = contact.email

    # Plain text fallback
    plain_text = f"""
    Hi {contact.name},

    Thanks for contacting Tempest Wash Co!

    We’ve received your request and will get back to you shortly.

    Message you sent:
    {contact.message}

    For urgent requests, call us at (310) 800-2444.

    — Tempest Wash Co Team
    """

    # HTML version
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
            <h2 style="color: #007BFF;">Thanks for reaching out, {contact.name}! 🙌</h2>
            <p>We’ve received your message and will get back to you shortly - most messages are answered within an hour during business hours.</p>

            <h4>Your Message:</h4>
            <blockquote style="background-color: #f1f1f1; padding: 15px; border-left: 4px solid #007BFF;">
                {contact.message}
            </blockquote>

            <p>If it’s urgent, tap the button below to call us:</p>

            <div style="text-align: center; margin: 20px 0;">
                <a href="tel:+13108002444" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px;">
                    📞 Call (310) 800-2444
                </a>
            </div>

            <p>Thanks again,<br><strong>Tempest Wash Co Team</strong></p>
            <p style="font-size: 14px; color: #777;">info@tempestwashco.com<br>(310) 800-2444</p>
            <p style="font-size: 0.9em; color: #888;">Sent via tempestwashco.com contact form</p>
        </div>
    </body>
    </html>
    """

    user_msg.set_content(plain_text)
    user_msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
            smtp.send_message(user_msg)
            print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# Services database
SERVICES_ = [
    {"id": "residential", "title": "Residential Pressure Washing", "icon": "fa-home",
     "description": "Driveways, patios, sidewalks, fences, siding. We clean it all with care and precision."},
    {"id": "commercial", "title": "Commercial Pressure Washing ", "icon": "fa-building",
     "description": "Storefronts, parking lots, warehouses, signage, and heavy-traffic concrete areas, spotless and professional."},
    {"id": "deep", "title": "Soft Washing", "icon": "fa-broom",
     "description": "Safe and effective cleaning for roofs, stucco, painted wood, and delicate surfaces."},
    {"id": "window", "title": "Window Cleaning", "icon": "fa-window-restore",
     "description": "Crystal-clear, streak-free window cleaning  interior and exterior."},
]

# Testimonials
TESTIMONIALS = [
    {"name": "Sarah Johnson", "rating": 5,
     "text": "Tempest Wash Co did an amazing job on my driveway and patio. Their team was professional, punctual, and used eco-friendly products, which I really appreciate.",
     "image": "tempestwashco.jpg"},
    {"name": "Michael Rodriguez", "rating": 5,
     "text": "Highly recommend for anyone needing pressure washing in LA!",
     "image": "tempestwashco.jpg"},
    {"name": "Emma Thompson", "rating": 5,
     "text": "Excellent service from start to finish! The team at Tempest Wash Co was thorough and careful with my home’s exterior. I love that they use environmentally safe cleaning solutions. My house looks spotless!",
     "image": "tempestwashco.jpg"},
]


@app.middleware("http")
async def redirect_to_www(request: Request, call_next):
    host = request.headers.get("host", "")
    if host.lower() == "tempestwashco.com":
        url = request.url.replace(netloc="www.tempestwashco.com")
        return RedirectResponse(url=str(url), status_code=301)
    return await call_next(request)


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": SERVICES_[:4],
        "testimonials": TESTIMONIALS
    })


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about_us.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.post("/contact")
async def handle_contact(form: ContactForm):
    try:
        send_email(form)
        return JSONResponse(content={"message": "Email sent"}, status_code=status.HTTP_200_OK)
    except Exception as e:
        print("Error sending email:", e)
        return JSONResponse(content={"message": "Failed to send email"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return templates.TemplateResponse("services.html", {
        "request": request,
        "services": SERVICES_
    })


@app.get("/services/residential", response_class=HTMLResponse)
async def services_residential(request: Request):
    return templates.TemplateResponse("residential.html", {"request": request})


@app.get("/services/commercial", response_class=HTMLResponse)
async def services_commercial(request: Request):
    return templates.TemplateResponse("commercial.html", {"request": request})


@app.get("/services/window-cleaning", response_class=HTMLResponse)
async def services_window_cleaning(request: Request):
    return templates.TemplateResponse("window-cleaning.html", {"request": request})


@app.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):
    return templates.TemplateResponse("verify.html", {"request": request})


@app.post("/verify", response_class=HTMLResponse)
async def verify_code(request: Request, code: str = Form(...)):
    if code == "123456":  # 🔐 You can change this to any secure code
        request.session["verified"] = True
        return RedirectResponse(url="/invoice", status_code=303)
    else:
        return templates.TemplateResponse("verify.html", {"request": request, "error": "Invalid passcode"})


@app.get("/invoice", response_class=HTMLResponse)
async def form(request: Request):
    if not request.session.get("verified"):
        return RedirectResponse(url="/verify")
    return templates.TemplateResponse("invoice_form.html", {"request": request})


@app.post("/generate_pdf", response_class=HTMLResponse)
async def generate_pdf_endpoint(
        request: Request,
        invoice_number: str = Form(...),
        customer_name: str = Form(...),
        customer_address: str = Form(...),
        customer_phone: str = Form(...),
        customer_email: str = Form(...),
        service_desc: List[str] = Form(...),
        quantity: List[int] = Form(...),
        unit_price: List[float] = Form(...),
):
    customer = {"name": customer_name, "address": customer_address, "phone": customer_phone}
    services = [{"desc": d, "qty": q, "price": p} for d, q, p in zip(service_desc, quantity, unit_price)]
    pdf_bytes = generate_pdf(customer, services, invoice_number)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    return templates.TemplateResponse("review.html", {
        "request": request,
        "pdf_data": pdf_b64,
        "invoice_number": invoice_number,
        "customer_email": customer_email,
        "customer_name": customer_name,
        "customer_address": customer_address,
        "customer_phone": customer_phone,
        "service_desc": service_desc,
        "quantity": quantity,
        "unit_price": unit_price,
    })


@app.post("/send_email")
async def send_email_endpoint(
        invoice_number: str = Form(...),
        customer_email: str = Form(...),
        customer_name: str = Form(...),
        customer_address: str = Form(...),
        customer_phone: str = Form(...),
        service_desc: List[str] = Form(...),
        quantity: List[int] = Form(...),
        unit_price: List[float] = Form(...),
):
    customer = {"name": customer_name, "address": customer_address, "phone": customer_phone}
    services = [{"desc": d, "qty": q, "price": p} for d, q, p in zip(service_desc, quantity, unit_price)]
    pdf_bytes = generate_pdf(customer, services, invoice_number)

    msg = EmailMessage()
    msg["From"] = "info@tempestwashco.com"
    msg["To"] = customer_email
    msg["Subject"] = f"Invoice #{invoice_number} from Tempest Wash Co – Thank You for Your Business"
    msg.set_content(
        f"Dear {customer_name},\n\nThank you for choosing Tempest Wash Co for your pressure washing needs!\n\n"
        f"Attached is your invoice for the recent service we provided.\n\nInvoice #:{invoice_number}\nService Date: {datetime.today().strftime('%m/%d/%Y')}\n\n"
        f"If you have any questions about the invoice or service, feel free to reply to this email or reach out at 310 800 2444.\n\n"
        f"We appreciate your business and would love to work with you again. \n\n"
        f"If you were happy with the service, a quick Google review would really help us grow!\n\n"
        f"Thanks again,\n"
        f"Tempest Wash Co\n"
        f"+ 1 310 800 2444\n"
        f"www.tempestwashco.com")
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"invoice_{invoice_number}.pdf")

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username="info@tempestwashco.com",
            password="zsnu tnqj nkzj jwgt ",
        )
    except Exception as e:
        return {"error": f"Email sending failed: {e}"}

    return RedirectResponse("/", status_code=303)


# 404 Error Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
