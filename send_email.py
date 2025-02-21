import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, sender, recipients, password):
    # Create the email message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Connect to Gmail's SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
        
    print("Email sent successfully!")

# Example usage
subject = "Test Email"
body = "Hello! This is a test email sent from Python."
sender = "your-email@gmail.com"
recipients = ["recipient@example.com"]
password = "your-app-password"

send_email(subject, body, sender, recipients, password)