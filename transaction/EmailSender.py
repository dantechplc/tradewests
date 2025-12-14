from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.models import CompanyProfile


def deposit_request_email(email_address, amount, client, payment_method):
    mail_subject = 'Deposit Request'
    to_email = email_address
    message = f"Hello Admin. \n client with  email {client}, sent a deposit request of {amount} via {payment_method}. " \
                  f"\n Kindly verify the deposit request.  "
    email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )

    return  email.send()


def InvestmentSuccess(*args, **kwargs):
    mail_subject = 'Investment Notice'
    email = kwargs.get('email')
    to_email = [email]
    message = render_to_string(
            "transaction/dsh/emails/invest_success.html",
            {
                "name": kwargs.get('name'),
                "amount":  kwargs.get('amount'),
                'plan':  kwargs.get('investment'),
                'expected_roi':  kwargs.get('expected_roi'),
                'next_payout': kwargs.get('next_payout'),
                'earning': kwargs.get('earning'),
                'date': kwargs.get('date'),
                "balance": kwargs.get('balance'),
                'trx_id': kwargs.get('trx_id'),
                "company": CompanyProfile.objects.first()
            },
        )
    email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
        )
    email.attach_alternative(message, 'text/html')
    email.content_subtype = 'html'
    return email.send()


def withdrawal_request_email(email_address, amount, client, payment_method):
    mail_subject = 'Withdrawal Request'
    to_email = email_address
    message = f"Hello Admin. \n client with  email {client}, sent a withdrawal request of {amount} via {payment_method}. " \
                  f"\n Kindly verify the withdrawal request.  "
    email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )

    return  email.send()


def kyc_email_sender(user, email):
    mail_subject = 'KYC Verify'
    to_email = email
    message = f"Hello Admin. \n client with  email {user}, sent KYC details. " \
                  f"\n Kindly verify the KYC request.  "
    email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
    return  email.send()


def roi_success_email(user, amount, balance, date, plan, trx_id, *args, **kwargs):
        date = date
        mail_subject = 'ROI Successful'
        message = render_to_string(
            "transaction/dsh/emails/roi_success_email.html",
            {
                "name": user.username,
                'amount': amount,
                'trx_id': trx_id,
                'date': date,
                 'plan': plan,
                'balance': balance,
                "company": CompanyProfile.objects.first()
            },
        )
        to_email = str(user)
        email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
        email.attach_alternative(message, 'text/html')
        email.content_subtype = 'html'
        email.mixed_subtype = 'related'
        return email.send()
