from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.models import CompanyProfile


def kyc_verified(email, name):
    mail_subject = 'Identity Verified'
    message = render_to_string(
                "accounts/boss/emails/kyc_verified.html",
                {
                    "name": name,
                    'company': CompanyProfile.objects.first()
                },
            )
    to_email = str(email)
    email = EmailMultiAlternatives(
    mail_subject, message, to=[to_email]
            )
    email.attach_alternative(message, 'text/html')
    email.content_subtype = 'html'
    email.mixed_subtype = 'related'

    return email.send()


def deposit_success(*args, **kwargs):
    mail_subject = 'Deposit Successful'
    message = render_to_string(
                "accounts/boss/emails/deposit_success.html",
                {
                    "name": kwargs.get('name'),
                    'amount': kwargs.get('amount'),
                    'trx_id:': kwargs.get('trx_id'),
                    'date': kwargs.get('date'),
                    'balance': kwargs.get('balance'),
                    'company': CompanyProfile.objects.first()
                },
            )
    to_email = str(kwargs.get('email'))
    email = EmailMultiAlternatives(
    mail_subject, message, to=[to_email]
            )
    email.attach_alternative(message, 'text/html')
    email.content_subtype = 'html'
    email.mixed_subtype = 'related'

    return email.send()


def withdraw_success(amount, trx_id, name, email, date, balance):
    mail_subject = 'Withdrawal Successful'
    message = render_to_string(
                "accounts/boss/emails/withdraw_success.html",
                {
                    "name": name,
                    'amount': amount,
                    'trx_id:': trx_id,
                    'date': date,
                    'balance': balance,
                    'company': CompanyProfile.objects.first()
                },
            )
    to_email = str(email)
    email = EmailMultiAlternatives(
    mail_subject, message, to=[to_email]
            )
    email.attach_alternative(message, 'text/html')
    email.content_subtype = 'html'
    email.mixed_subtype = 'related'
    return email.send()
