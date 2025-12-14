from datetime import timedelta

from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField

from accounts.utils import generate_ref_code
from .constants import *
from accounts.models import Client, Investment, PaymentMethods


# Create your models here.


class Transactions(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transaction')
    amount = MoneyField(max_digits=19, decimal_places=2, null=True, )
    fees = MoneyField(max_digits=19, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(blank=True, null=True, )
    trx_id = models.CharField(max_length=100000000, blank=True, unique=True)
    investment_name = models.ForeignKey(Investment, blank=True, null=True, on_delete=models.CASCADE)
    payment_methods = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=200, choices=status, blank=True, default='pending')
    receipt_upload = models.ImageField(blank=True, null=True, upload_to='receipts/')
    wallet_address = models.CharField(max_length=900, blank=True, null=True)
    transaction_type = models.CharField(max_length=200, blank=True, choices=TRANSACTION_TYPE_CHOICES)
    payment_description = models.TextField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.user)

    def ROI(amount, rate, days):
        interest = (amount * rate / 100) * days + amount
        return interest

    def expiry_date(amount, rate, days):
        expected_days = ((amount * rate / 100) * days + amount) / (amount * rate / 100)
        return round(expected_days)

    def earning(amount, rate):
        earning = amount * rate / 100
        return earning

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()  # Set date manually if not already set
        if self.trx_id == "":
            code = generate_ref_code() + str(self.user.id)
            self.trx_id = code
        super().save(*args, **kwargs)

    def add_business_days(start_date, days):
        current_date = start_date
        added_days = 0

        while added_days < days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # 0=Mon, 6=Sun
                added_days += 1

        return current_date
    def get_next_payout(today):
        today = timezone.now()

        if today.weekday() == 5:
            # Saturday → next Monday
            return today + timedelta(days=2)
        elif today.weekday() == 6:
            # Sunday → next Monday
            return today + timedelta(days=1)
        else:
            # Mon–Fri → just add 1 day
            return today + timedelta(days=1)