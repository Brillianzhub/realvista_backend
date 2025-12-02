from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.core.files.storage import default_storage
from django.conf import settings
import os


def generate_invoice(property_purchase):
    filename = f"invoice_{property_purchase.id}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Realvista Properties Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Invoice ID: {property_purchase.id}")
    c.drawString(50, height - 120,
                 f"Date: {property_purchase.created_at.strftime('%Y-%m-%d')}")
    c.drawString(50, height - 140,
                 f"Client Name: {property_purchase.user.name}")
    c.drawString(50, height - 160, f"Email: {property_purchase.user.email}")
    c.drawString(50, height - 180,
                 f"Property: {property_purchase.property.title}")
    c.drawString(50, height - 200,
                 f"Payment Plan: {property_purchase.payment_plan.name}")
    c.drawString(50, height - 220,
                 f"Total Amount: ₦{property_purchase.total_amount}")
    c.drawString(50, height - 240,
                 f"Amount Paid: ₦{property_purchase.amount_paid}")
    c.drawString(50, height - 260,
                 f"Balance: ₦{property_purchase.remaining_balance()}")

    # Auto-signature
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.blue)
    c.drawString(50, height - 320, "Signed by:")
    c.drawString(50, height - 340, "Realvista Team")

    # Save PDF
    c.save()
    return file_path
