from io import BytesIO
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_invoice_pdf(user_name, user_email, project_name, quantity, cost_per_slot, total_amount):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)

    x = 100
    y = 750
    line_spacing = 20

    pdf_canvas.setFont("Helvetica-Bold", 14)
    pdf_canvas.drawString(x, y, f"INVOICE")
    y -= line_spacing

    # Invoice details
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, f"Invoice No: 001234")
    y -= line_spacing
    pdf_canvas.drawString(x, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    y -= line_spacing * 2

    # Bill To
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(x, y, "BILL TO:")
    y -= line_spacing
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, user_name)
    y -= line_spacing
    pdf_canvas.drawString(x, y, user_email)
    y -= line_spacing * 2

    # From
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(x, y, "FROM:")
    y -= line_spacing
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, "Realvista GmbH")
    y -= line_spacing * 2

    # Project Details
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(x, y, "PROJECT DETAILS:")
    y -= line_spacing
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, f"Project Name: {project_name}")
    y -= line_spacing
    pdf_canvas.drawString(x, y, f"Number of Slots Purchased: {quantity}")
    y -= line_spacing
    pdf_canvas.drawString(x, y, f"Cost Per Slot: ${cost_per_slot}")
    y -= line_spacing
    pdf_canvas.drawString(x, y, f"Total Amount: ${total_amount}")
    y -= line_spacing * 2

    # Payment Instructions
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(x, y, "PAYMENT INSTRUCTIONS:")
    y -= line_spacing
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, "Bank Name: Commerzbank")
    y -= line_spacing
    pdf_canvas.drawString(x, y, "Account Name: Realvista GmbH")
    y -= line_spacing
    pdf_canvas.drawString(x, y, "IBAN: DE06 XXXXX XXXXX XXXXX")
    y -= line_spacing
    pdf_canvas.drawString(x, y, f"Reference: {user_name or 'Invoice 001234'}")
    y -= line_spacing * 2

    # Notes
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(x, y, "NOTES:")
    y -= line_spacing
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(
        x, y, "- Please ensure payment is made within 7 business days.")
    y -= line_spacing
    pdf_canvas.drawString(
        x, y, "- Bank transfers may take up to 2 working days to process.")
    y -= line_spacing * 2

    # Footer
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x, y, "Thank you for trusting Realvista GmbH!")

    # Finalize and save the PDF
    pdf_canvas.save()
    buffer.seek(0)

    return buffer


buffer = generate_invoice_pdf(
    user_name="John Doe",
    user_email="john.doe@example.com",
    project_name="Website Development",
    quantity=5,
    cost_per_slot=200,
    total_amount=1000
)

# Save the PDF to a file for testing (optional)
with open("invoice.pdf", "wb") as f:
    f.write(buffer.read())
