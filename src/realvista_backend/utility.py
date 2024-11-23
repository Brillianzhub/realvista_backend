from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from reportlab.pdfgen import canvas
from datetime import datetime


def send_invoice_email(user_name, user_email, project_name, quantity, cost_per_slot, total_amount):
    try:
        # Generate PDF invoice
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
        pdf_canvas.drawString(
            x, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
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
        pdf_canvas.drawString(
            x, y, f"Reference: {user_name or 'Invoice 001234'}")
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

        # Create email
        subject = f"Invoice for Your Interest in the Project: {project_name}"
        message = (
            f"Dear {user_name},\n\n"
            f"Thank you for your interest in our project, {project_name}. We are delighted to assist you in completing your payment process.\n\n"
            "Please find attached a PDF invoice with all the necessary payment details. Kindly download and print the invoice for your records. "
            "You can proceed to make the payment via bank transfer using the details provided in the invoice.\n\n"
            "Note: Payments made through bank transfer may take up to two working days for verification.\n\n"
            "If you have any questions or need further assistance, feel free to reach out to us at support@example.com.\n\n"
            "Thank you for choosing Realvista GmbH. We look forward to serving you.\n\n"
            "Warm regards,\n"
            "Realvista Team"
        )
        email = EmailMessage(
            subject,
            message,
            "no-reply@realvista.com",
            [user_email],
        )

        # Attach the PDF
        email.attach(f"Invoice_{project_name}.pdf",
                     buffer.getvalue(), "application/pdf")

        # Send the email
        email.send()
        return {"success": True, "message": "Invoice sent successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
