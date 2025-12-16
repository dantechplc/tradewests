from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone
from djmoney.money import Money

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



def investment_expired_check():
    # Get both querysets
    qs1 = Investment_profile.objects.filter(expired=False, status='Active')
    today = timezone.now()

    # Chain them together into one iterable


    for investment in qs1:
        # expected_amount = doc.expected_roi
        # amount_earned = doc.amount_earned
        # expiry_date = doc.expiry_date
        if investment.expiry_date <= today:
            expected = investment.expected_roi
            earned = investment.amount_earned
            account_user = investment.user
            account_client = Account.objects.get(user=account_user)

            if earned < expected:
                difference =  Money(
                                    expected.amount - earned.amount,
                                    earned.currency
                                )


                print(
                        f"⚠ Correcting ROI for Investment {investment.id}: "
                        f"Missing {difference}"
                    )

                    # Atomic update (VERY IMPORTANT)
                # with transaction.atomic():
                account_client.roi_balance += difference
                account_client.total_roi_received += difference

                investment.amount_earned = expected
                investment.status = "Expired"
                investment.expired = True


                account_client.save(update_fields=[
                            "roi_balance",
                            "total_roi_received"
                        ])
                investment.save(update_fields=[
                            "amount_earned",
                            "status",
                            "expired"
                        ])
                 # Notify admin
            company_email = CompanyProfile.objects.first()
            email = company_email.forwarding_email
            mail_subject = "Expired Investment"
            to_email = str(email)
            message1 =f"""
                Hello Admin, the user with email {account_user} investment of {investment.amount_invested} has expired
                and has earned {investment.amount_earned}
            
                """
            email = EmailMultiAlternatives(mail_subject, message1, to=[to_email])
            email.attach_alternative(message1, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()




import os
import zipfile
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone


def email_database_backup():
    """
    Daily database backup cron:
    - Zips db.sqlite3
    - Emails it as attachment
    - Deletes zip after sending
    """

    try:
        BASE_DIR = settings.BASE_DIR
        today = timezone.now().strftime("%Y-%m-%d")

        db_path = os.path.join(BASE_DIR, "db.sqlite3")
        backup_dir = os.path.join(BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        zip_path = os.path.join(backup_dir, f"db_backup_{today}.zip")

        # 🔹 ZIP DATABASE
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db_path, "db.sqlite3")

        # 🔹 SEND EMAIL
        email = EmailMessage(
            subject=f"Tradewests Database Backup - {today}",
            body="Attached is the automated database backup.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["chukwujidan@gmail.com"],  # change if needed
        )

        email.attach_file(zip_path)
        email.send(fail_silently=False)

        # 🔹 CLEAN UP ZIP FILE
        os.remove(zip_path)

        print("✅ Database backup emailed successfully")

    except Exception as e:
        print("❌ Database backup failed:", str(e))

