from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from accounts.models import Investment_profile, Client, Account, Investment, CompanyProfile
from transaction import EmailSender
from transaction.models import Transactions


def daily_roi():
    today = timezone.now()
    print("✅ Cron daily_roi ran at", today)

    investments = Investment_profile.objects.filter(status='Active', next_payout__lte=timezone.now())

    for investment in investments:
        print(f"Processing investment {investment.id} for {investment.user}, next payout: {investment.next_payout}, today: {today}")

        if investment.next_payout and investment.next_payout <= today:
            account_user = investment.user
            account_client = Account.objects.get(user=account_user)

            # Add interest
            interest = investment.earning
            account_client.roi_balance += interest
            account_client.total_roi_received += interest

            account_client.save(update_fields=['roi_balance', 'total_roi_received'])

            # Update investment profile
            investment.amount_earned += interest
            investment.next_payout = Transactions.get_next_payout(today)  # define this helper
            investment.save(update_fields=['amount_earned', 'next_payout'])
             # Record transaction
            trx = Transactions.objects.create(
                user=account_client.user,
                amount=interest,
                status='Successful',
                investment_name=Investment.objects.get(name=investment.investment),
                transaction_type='ROI',
                date=today,
            )

            # Send ROI email
            EmailSender.roi_success_email(
                user=account_user.user,
                amount=interest,
                balance=account_client.roi_balance,
                date=today,
                plan=Investment.objects.get(name=investment.investment),
                trx_id=trx.trx_id,
            )
            print("✅ ROI email sent", today)

            # =========================
        # 2️⃣ EXPIRY AUTO-CORRECTOR
        # =========================
        if investment.expiry_date <= today:
            expected = investment.expected_roi
            earned = investment.amount_earned
            account_user = investment.user
            account_client = Account.objects.get(user=account_user)

            if earned < expected:
                difference = expected - earned

                print(
                        f"⚠ Correcting ROI for Investment {investment.id}: "
                        f"Missing {difference}"
                    )

                    # Atomic update (VERY IMPORTANT)
                with transaction.atomic():
                    account_client.roi_balance += difference
                    account_client.total_roi_received += difference

                    investment.amount_earned = expected
                    investment.status = "Expired"


                    account_client.save(update_fields=[
                            "roi_balance",
                            "total_roi_received"
                        ])
                    investment.save(update_fields=[
                            "amount_earned",
                            "status"
                        ])
        else:
                # No correction needed, just expire it
                investment.status = "Expired"
                investment.save(update_fields=["status"])





def investment_expired_check():
    # Get both querysets
    qs1 = Investment_profile.objects.filter(expired=False, status='Active')


    # Chain them together into one iterable


    for doc in qs1:
        expected_amount = doc.expected_roi
        amount_earned = doc.amount_earned
        expiry_date = doc.expiry_date

        # Condition: ROI reached OR expiry date passed
        if amount_earned >= expected_amount or (expiry_date and expiry_date <= timezone.now()):
            doc.expired = True
            doc.status = 'Expired'
            doc.save(update_fields=['expired', 'status'])

            print('✅ Expired investment found for', doc.user)

            # Update related transaction
            Transactions.objects.filter(pk=doc.trx_id).update(status='Expired')

            # Notify admin
            company_email = CompanyProfile.objects.first()
            email = company_email.forwading_email
            mail_subject = "Expired Investment"
            to_email = str(email)
            message1 = (
                f'Hello Admin. {doc.user} {doc.investment} Investment plan of '
                f'{doc.amount_invested} ({getattr(doc, "amount_invested", None)}) has expired today.'
            )
            email = EmailMultiAlternatives(mail_subject, message1, to=[to_email])
            email.attach_alternative(message1, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()


