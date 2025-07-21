# main.py

import base64
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import List, Optional

import aiosmtplib
import frontmatter
import markdown
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, Form
from fastapi import File, UploadFile, HTTPException, Depends
from fastapi import status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr, BaseModel
from slugify import slugify
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from database import get_db, init_db
from models.blog import BlogPost
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

ADMIN_SECRET_CODE = "1234"  # Change to your secure code or better store in env var


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


def create_quote_email(to_email: str, total: float, breakdown: str, message: str) -> EmailMessage:
    breakdown_html = "".join(f"<li>{line}</li>" for line in breakdown)
    breakdown_text = "\n".join(f"- {line}" for line in breakdown)

    email = EmailMessage()
    email['Subject'] = "Your Tempest Wash Co Quote - Valid for 7 Days"
    email['From'] = "info@tempestwashco.com"  # Change to your sender email
    email['To'] = to_email

    email.set_content(f"""
Hi,

Thank you for requesting a quote from Tempest Wash Co!

Here is your estimated price based on the details you provided:

Total Estimated Cost: ${total}

Breakdown:
{breakdown_text}

Additional Details:
{message if message else 'No additional details provided.'}

Please note: If the information you entered is accurate, this quote is valid for 7 days and will not change during this period.

Feel free to contact us if you have any questions or want to schedule your service.

Best regards,
Tempest Wash Co Team
Phone: (310) 800-2444
Email: info@tempestwashco.com
Website: https://www.tempestwashco.com
""")

    # Also set HTML alternative for nicer formatting
    email.add_alternative(f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Thank you for requesting a quote from Tempest Wash Co!</h2>
    <p>Here is your estimated price based on the details you provided:</p>
    <p><strong>Total Estimated Cost: ${total}</strong></p>
    <h3>Breakdown:</h3>
    <ul>
      {breakdown_html}
    </ul>
    <h3>Additional Details:</h3>
    <p>{message if message else 'No additional details provided.'}</p>
    <p><em>Please note:</em> If the information you entered is accurate, this quote is valid for <strong>7 days</strong> and will not change during this period.</p>
    <p>If you have any questions or want to schedule your service, please contact us anytime.</p>
    <p>Best regards,<br>
    <strong>Tempest Wash Co Team</strong><br>
    Phone: (310) 800-2444<br>
    Email: <a href="mailto:info@tempestwashco.com">info@tempestwashco.com</a><br>
    Website: <a href="https://www.tempestwashco.com">www.tempestwashco.com</a></p>
  </body>
</html>
""", subtype='html')

    return email


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
    {"id": "window-cleaning", "title": "Window Cleaning", "icon": "fa-window-restore",
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
     "text": "Excellent service from start to finish! The team at Tempest Wash was thorough and careful with my home’s exterior. My house looks spotless!",
     "image": "tempestwashco.jpg"},
]

RATES = {
    "house_1story": 0.25,  # per sq ft
    "house_2story": 0.35,
    "driveway_base": 129,  # flat up to 400 sq ft
    "driveway_rate": 0.35,  # per sq ft over 400
    "sidewalk_linear": 1.50,  # per linear ft
    "sidewalk_area": 0.40,  # per sq ft
    "patio": 0.40,  # per sq ft
    "fence": 2.50,  # per linear ft
    "gutter": 2.00,  # per linear ft
    "roof": 0.45,  # per sq ft
}


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


@app.get("/admin/upload-blog-md", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    return templates.TemplateResponse("admin_upload_blog.html", {"request": request})


@app.post("/admin/upload-blog-md")
async def upload_blog_md(
        file: UploadFile = File(...),
        secret_code: str = Form(...),
        db: Session = Depends(get_db)
):
    if secret_code != ADMIN_SECRET_CODE:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid secret code")

    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only Markdown files allowed")

    contents = await file.read()
    text = contents.decode("utf-8")

    post = frontmatter.loads(text)
    meta = post.metadata

    title = meta.get("title")
    created_at_str = meta.get("created_at")
    slug = meta.get("slug")

    if not title:
        raise HTTPException(status_code=400, detail="Missing title in frontmatter")

    if not slug:
        slug = slugify(title)

    try:
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d") if created_at_str else datetime.utcnow()
    except:
        created_at = datetime.utcnow()

    markdown_content = post.content

    existing = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    blog_post = BlogPost(
        title=title,
        slug=slug,
        content=markdown_content,
        created_at=created_at
    )

    db.add(blog_post)
    db.commit()
    db.refresh(blog_post)

    return {"message": "Blog uploaded", "slug": slug}


@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, db: Session = Depends(get_db)):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

    def create_excerpt(md_text, length=75):
        # Convert markdown to HTML
        html = markdown.markdown(md_text, extensions=['extra', 'codehilite', 'toc', 'tables', 'fenced_code'])
        # Strip tags and get plain text using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        # Truncate text to desired length
        excerpt_text = (text[:length] + '...') if len(text) > length else text
        return excerpt_text

    # Add an 'excerpt' attribute to each post object dynamically
    for post in posts:
        post.excerpt = create_excerpt(post.content)

    return templates.TemplateResponse("blog.html", {"request": request, "posts": posts})


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")

    content_html = markdown.markdown(
        post.content,
        extensions=['extra', 'codehilite', 'toc', 'tables', 'fenced_code']
    )

    return templates.TemplateResponse("blog_detail.html", {
        "request": request,
        "post": post,
        "content_html": content_html
    })


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


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms_of_use(request: Request):
    return templates.TemplateResponse("terms_of_service.html", {"request": request})


@app.get("/how-to-estimate", response_class=HTMLResponse)
async def how_to_estimate(request: Request):
    return templates.TemplateResponse("how_to_estimate.html", {"request": request})


@app.get("/quote", response_class=HTMLResponse)
async def get_quote_form(request: Request):
    return templates.TemplateResponse("quote_form.html", {"request": request})


@app.post("/quote", response_class=HTMLResponse)
async def post_quote(
        request: Request,
        email: str = Form(...),
        services: Optional[List[str]] = Form(None),
        house1_sqft: Optional[float] = Form(0),
        house2_sqft: Optional[float] = Form(0),
        driveway_sqft: Optional[float] = Form(0),
        sidewalk_linear_ft: Optional[float] = Form(0),
        sidewalk_sqft: Optional[float] = Form(0),
        patio_sqft: Optional[float] = Form(0),
        fence_ft: Optional[float] = Form(0),
        gutter_ft: Optional[float] = Form(0),
        roof_sqft: Optional[float] = Form(0),
        message: Optional[str] = Form(""),
):
    # Defensive cleanup and defaults
    if services is None:
        services = []

    total = 0.0
    breakdown = []

    # House 1-story
    if "house_1story" in services and house1_sqft:
        cost = house1_sqft * RATES["house_1story"]
        total += cost
        breakdown.append(f"1-story house ({house1_sqft} sq.ft.): ${cost:.2f}")

    # House 2-story
    if "house_2story" in services and house2_sqft:
        cost = house2_sqft * RATES["house_2story"]
        total += cost
        breakdown.append(f"2-story house ({house2_sqft} sq.ft.): ${cost:.2f}")

    # Driveway
    if "driveway" in services and driveway_sqft:
        if driveway_sqft <= 400:
            cost = RATES["driveway_base"]
        else:
            cost = RATES["driveway_base"] + (driveway_sqft - 400) * RATES["driveway_rate"]
        total += cost
        breakdown.append(f"Driveway ({driveway_sqft} sq.ft.): ${cost:.2f}")

    # Sidewalk (linear feet)
    if "sidewalk" in services and sidewalk_linear_ft:
        cost = sidewalk_linear_ft * RATES["sidewalk_linear"]
        total += cost
        breakdown.append(f"Sidewalk length ({sidewalk_linear_ft} ft): ${cost:.2f}")

    # Sidewalk (area)
    if "sidewalk" in services and sidewalk_sqft:
        cost = sidewalk_sqft * RATES["sidewalk_area"]
        total += cost
        breakdown.append(f"Sidewalk area ({sidewalk_sqft} sq.ft.): ${cost:.2f}")

    # Patio
    if "patio" in services and patio_sqft:
        cost = patio_sqft * RATES["patio"]
        total += cost
        breakdown.append(f"Patio ({patio_sqft} sq.ft.): ${cost:.2f}")

    # Fence
    if "fence" in services and fence_ft:
        cost = fence_ft * RATES["fence"]
        total += cost
        breakdown.append(f"Fence ({fence_ft} ft): ${cost:.2f}")

    # Gutter
    if "gutter" in services and gutter_ft:
        cost = gutter_ft * RATES["gutter"]
        total += cost
        breakdown.append(f"Gutter ({gutter_ft} ft): ${cost:.2f}")

    # Roof
    if "roof" in services and roof_sqft:
        cost = roof_sqft * RATES["roof"]
        total += cost
        breakdown.append(f"Roof wash ({roof_sqft} sq.ft.): ${cost:.2f}")

    email_msg = create_quote_email(email, total, breakdown, message)

    # Send email via your SMTP server
    try:
        await aiosmtplib.send(
            email_msg,
            hostname=SMTP_SERVER,
            port=587,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS,
        )
    except Exception as e:
        print("Email sending failed:", e)
    return templates.TemplateResponse(
        "quote_form.html",
        {
            "request": request,
            "success": True,
            "total": f"{total:.2f}",
            "breakdown": breakdown,
        },
    )


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


# 1. Show all blog posts with delete links
@app.get("/admin/delete-blog", response_class=HTMLResponse)
async def delete_blog_list(request: Request, db: Session = Depends(get_db)):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
    return templates.TemplateResponse("admin_delete_blog_list.html", {"request": request, "posts": posts})


# 2. Show confirmation form to enter code before deleting
@app.get("/admin/delete-blog/{slug}", response_class=HTMLResponse)
async def delete_blog_confirm(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return templates.TemplateResponse("admin_delete_blog_confirm.html", {"request": request, "post": post})


# 3. Handle form submission and delete if code is valid
@app.post("/admin/delete-blog/{slug}")
async def delete_blog_post(request: Request, slug: str, secret_code: str = Form(...), db: Session = Depends(get_db)):
    if secret_code != ADMIN_SECRET_CODE:
        # Show error page or return with error message
        return templates.TemplateResponse(
            "admin_delete_blog_confirm.html",
            {"request": request, "post": db.query(BlogPost).filter(BlogPost.slug == slug).first(),
             "error": "Invalid secret code"},
            status_code=403,
        )
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    db.delete(post)
    db.commit()
    return templates.TemplateResponse("admin_delete_blog_success.html", {"request": request, "title": post.title})


# 404 Error Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # For certain status codes, render the error template
    if exc.status_code in {403, 404, 500}:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": exc.detail
            },
            status_code=exc.status_code,
        )
    # For other HTTPExceptions fallback to default JSON response
    return await http_exception_handler(request, exc)


@app.on_event("startup")
async def on_startup():
    init_db()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
