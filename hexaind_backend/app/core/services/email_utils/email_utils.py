from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, To)
import traceback
from azure.communication.email import EmailClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from enum import Enum

from app.config.env_vars import environment, get_secret

logger = logging.getLogger(__package__)

class EmailMethod(str,Enum):
    SENDGRID='sendgrid'
    SMTP='smtp'
    AZURE_EMAIL_COMMUNICATION='azure_email_communication'

def send_simple_mail(to_mail_ids: list, html_content: str = "<strong>Test Mail from Databrick Technologies (Python API)</strong>", mail_subject: str = "From Databrick Technologies", from_mail_id: str = 'Databrick <no-reply@databrick.tech>', is_personal: bool = True):
    try:
        if to_mail_ids is None or len(to_mail_ids) == 0:
            return False
        is_mails_sent = False
        send_email_using_method = environment.send_email_using
        if send_email_using_method == EmailMethod.SENDGRID:
            is_mails_sent =  send_mail_using_send_grid(to_mail_ids, html_content, mail_subject, from_mail_id, is_personal)
        elif send_email_using_method == EmailMethod.SMTP:
            is_mail_sent = True
            for to_mail_id in to_mail_ids:
                if send_mail_using_smtp(to_mail_id, mail_subject, html_content, from_mail_id) == False:
                    is_mail_sent = False
            is_mails_sent =  is_mail_sent
        elif send_email_using_method == EmailMethod.AZURE_EMAIL_COMMUNICATION:
            is_mails_sent = send_mail_using_azure_communication(to_mail_ids, mail_subject, html_content, is_personal)
        else:
            raise KeyError(f"Could not find the email sending implementation for {send_email_using_method}")
        # Add more APIs or methods if any

        logger.info(f"Mail sent status:{is_mails_sent} to {to_mail_ids} using implementation {send_email_using_method}")
        return is_mails_sent
    except Exception as e:
        traceback.print_exc()
        logger.exception(f"SendGrid API- Failed to send mails to {to_mail_ids} With subject:{mail_subject}")
        return False

def send_mail_using_send_grid(to_mail_ids: list, html_content: str, mail_subject: str, from_mail_id: str, is_personal: bool):
    to_mail_list = []

    for mail_id in to_mail_ids:
        to_mail_list.append(To(mail_id))

    message = Mail(
        from_email=from_mail_id,
        to_emails=to_mail_list,
        subject=mail_subject,
        is_multiple=is_personal,
        html_content=html_content)

    sg = SendGridAPIClient(environment.sendgrid_api_key)
    response = sg.send(message)
    if response.status_code >= 200 and response.status_code < 300:
        return True
    return False

def send_mail_using_smtp( receiver_email, subject, message, from_name=''):
    is_mail_sent = False
    try:
        smtp_det_csv = environment.smtp_server_port_email_password_csv
        smtp_server_port_email_password_list = smtp_det_csv.split(',')
        
        smtp_server= smtp_server_port_email_password_list[0].strip()
        smtp_port= int(smtp_server_port_email_password_list[1].strip())
        sender_email = smtp_server_port_email_password_list[2].strip()
        sender_password = smtp_server_port_email_password_list[3].strip()

        msg = MIMEMultipart()
        from_txt = f"{from_name}" if from_name else sender_email

        msg['From'] = from_txt
        msg['To'] = receiver_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'html'))
    
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        is_mail_sent = True
    except Exception:
        logger.exception(f"SMTP - Failed to send smtp email to {receiver_email}, Subject:{subject}")
    return is_mail_sent

def send_mail_using_azure_communication(to_mail_ids: list, mail_subject: str, html_content: str, is_personal: bool = True):
    if to_mail_ids == None or len(to_mail_ids) == 0:
        return False
    try:
        connection_string = get_secret('azure-email-conn-string') 
        reply_email = get_secret('azure-comm-reply-email')

        if connection_string is None or reply_email is None:
            raise KeyError('Azure Communication secrets not available Please check secrets azure-email-conn-string & azure-comm-reply-email')

        email_client = EmailClient.from_connection_string(connection_string)

        send_mail_as_bcc = True

        if len(to_mail_ids) == 1 or is_personal == False:
            send_mail_as_bcc = False

        rec_emails_dict = []

        for mail_id in to_mail_ids:
            rec_emails_dict.append({"address": mail_id})

        message = {
            "content": {
                "subject": mail_subject,
                "plainText": "",
                "html": html_content
            },
            "recipients": {
                "to": []
            },
            "senderAddress": reply_email
        }
        
        if len(to_mail_ids) == 1 or send_mail_as_bcc:
            message['recipients']['to'] = rec_emails_dict
        else:
            message['recipients']['bcc'] = rec_emails_dict
        
        poller = email_client.begin_send(message)
        result = poller.result()

        if result['error'] is None:
            return True
        else:
            return False

    except Exception:
         logger.exception(f"Azure Email Communication API - Failed to send mails to {to_mail_ids} With subject:{mail_subject}")
         return False
