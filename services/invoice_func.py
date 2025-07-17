from fpdf import FPDF


class PDFWithProfessionalDesign(FPDF):
    def header(self):
        self.set_fill_color(0, 102, 204)
        self.rect(0, 0, 210, 35, 'F')
        try:
            self.image("logo.png", 10, 7, 20)
        except:
            pass
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 16)
        self.set_xy(35, 10)
        self.cell(0, 7, "Tempest Wash Co.", ln=1)
        self.set_font("Arial", "", 10)
        self.set_x(35)
        self.cell(0, 6, "Pressure Washing | www.tempestwashco.com", ln=1)
        self.set_x(35)
        self.cell(0, 6, "Call: 310-800-2444 | Email: info@tempestwashco.com", ln=1)

    def footer(self):
        self.set_y(-20)
        self.set_fill_color(0, 102, 204)
        self.rect(0, self.get_y(), 210, 20, 'F')
        self.set_y(-15)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "Thank you for choosing Tempest Wash Co. We appreciate your business.", 0, 0, "C")


def generate_pdf(customer, services, invoice_number: str):
    pdf = PDFWithProfessionalDesign()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(1)
    pdf.line(10, 40, 200, 40)
    pdf.ln(10)

    pdf.set_xy(130, 42)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Invoice #: {invoice_number}", 0, 1, "R")

    pdf.set_xy(130, 52)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Bill To:", 0, 1, "R")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, customer['name'], 0, 1, "R")
    pdf.cell(0, 6, customer['address'], 0, 1, "R")
    pdf.cell(0, 6, "Phone: " + customer['phone'], 0, 1, "R")
    pdf.ln(12)

    y = pdf.get_y()
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.4)
    pdf.line(10, y, 200, y)
    pdf.ln(6)

    pdf.set_fill_color(255, 222, 89)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(80, 10, "Description", 1, 0, "C", fill=True)
    pdf.cell(30, 10, "Quantity", 1, 0, "C", fill=True)
    pdf.cell(40, 10, "Unit Price", 1, 0, "C", fill=True)
    pdf.cell(40, 10, "Total", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 11)
    subtotal = 0
    for s in services:
        desc = s['desc']
        qty = int(s['qty'])
        price = float(s['price'])
        total = qty * price
        subtotal += total
        pdf.cell(80, 10, desc, 1, 0)
        pdf.cell(30, 10, str(qty), 1, 0, "C")
        pdf.cell(40, 10, f"${price:.2f}", 1, 0, "C")
        pdf.cell(40, 10, f"${total:.2f}", 1, 1, "C")

    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(150, 8, "Subtotal", 0, 0, "R")
    pdf.set_font("Arial", "", 11)
    pdf.cell(40, 8, f"${subtotal:.2f}", 0, 1, "R")

    pdf.set_font("Arial", "B", 11)
    pdf.cell(150, 8, "Discount", 0, 0, "R")
    pdf.set_font("Arial", "", 11)
    pdf.cell(40, 8, "-$0.00", 0, 1, "R")

    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(150, 10, "Total Paid", 0, 0, "R")
    pdf.cell(40, 10, f"${subtotal:.2f}", 0, 1, "R")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Payment Terms", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "This invoice has been paid in full. No further action is required.")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Accepted Payment Methods", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Zelle: 309-262-9545", 0, 1)
    pdf.cell(0, 6, "Cash/Check: 1948 20th St Apt 202, Santa Monica, CA 90404", 0, 1)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Authorized Signature", 0, 1)
    try:
        pdf.image("static/images/signature.png", x=140, y=pdf.get_y(), w=50)
        pdf.ln(25)
    except:
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "[Signature image not found]", 0, 1)
        pdf.set_text_color(0, 0, 0)

    return pdf.output(dest='S').encode('latin1')
