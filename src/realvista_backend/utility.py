from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from reportlab.pdfgen import canvas


def send_invoice_email(user_email, project_name, total_amount, user_name):
    try:
        # Generate PDF invoice
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)
        pdf_canvas.drawString(100, 800, f"Invoice for {project_name}")
        pdf_canvas.drawString(100, 780, f"Customer Name: {user_name}")
        pdf_canvas.drawString(100, 760, f"Total Amount: ${total_amount}")
        pdf_canvas.drawString(100, 740, "Bank Name: Commerzbank")
        pdf_canvas.drawString(100, 720, "Account Name: Realvista GmbH")
        pdf_canvas.drawString(100, 700, "IBAN: DE06 ...........")
        pdf_canvas.drawString(
            100, 680, "Note: Payments through Bank transfers may take up to 2 working days.")
        pdf_canvas.save()
        buffer.seek(0)

        # Create email
        subject = f"Invoice for Your Interest in the Project: {project_name}"
        message = (
            f"Dear {user_name},\n\n"
            f"Thank you for your interest in our project, f'{project_name}'. We are delighted to assist you in completing your payment process.\n\n"
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
            "no-reply@yourcompany.com",
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
