import uuid
from io import BytesIO

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill
import qrcode
from accounts.constants import *
from accounts.utils import generate_ref_code
from accounts.manager import UserManager


# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(
        _('username'),
        max_length=200,
        blank=True,
        default="",      # ✅ empty string instead of None
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    saved_password = models.CharField(_("password"), max_length=200, null=True, blank=True, default='0000')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.email)

    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the user's first name."""
        return self.first_name

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']


class Client(models.Model):
    user = models.OneToOneField(
        User,
        related_name='client',
        on_delete=models.CASCADE,
    )
    profile_pic = models.ImageField(
        upload_to='client/profile_pic',
        default='client/profile_pic/avartar.png',
        null=True, blank=True
    )
    profile_pic_thumbnail = ImageSpecField(
        source='profile_pic',
        processors=[ResizeToFill(100, 100)],
        format="JPEG",
        options={'quality': 60}
    )
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=200, blank=True, null=True, choices=GENDER_CHOICE)
    dob = models.DateTimeField(blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)
    country = CountryField(blank_label='(select country)', blank=True, null=True, default='US')
    zip = models.PositiveIntegerField(blank=True, null=True)
    Verification_status = models.CharField(
        max_length=200, choices=verification_status, blank=True, default='Unverified'
    )
    date_joined = models.DateTimeField(blank=True, null=True, )
    phone_number = models.CharField(max_length=15, blank=True)
    referral_code = models.CharField(blank=True, max_length=6, unique=True)
    recommended_by = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='referrals'
    )
    account_password = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = generate_ref_code()
        super().save(*args, **kwargs)



class Account(models.Model):
    user = models.OneToOneField(
        "Client",
        on_delete=models.CASCADE,
        related_name="account"
    )

    trx_id = models.CharField(max_length=300, blank=True, null=True)

    main_balance = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    book_balance = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    balance_status = models.CharField(max_length=200, choices=status, null=True, blank=True, default="pending")

    total_amount_investment = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    total_amount_deposited = MoneyField(max_digits=19,  blank=True,decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    bonus = MoneyField(max_digits=19, decimal_places=2, blank=True, default_currency="USD", default=Money(0, "USD"))

    transaction_pin = models.CharField(max_length=128, null=True, blank=True)  # hashed pin storage

    total_expected_roi = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    total_roi_received = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    total_amount_withdrawn = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))
    roi_balance = MoneyField(max_digits=19, blank=True, decimal_places=2, default_currency="USD", default=Money(0, "USD"))

    last_deposit_date = models.DateTimeField(blank=True, null=True)
    last_withdrawal_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Account({self.user})"

    # --- Transaction PIN helpers ---
    def set_transaction_pin(self, raw_pin: str):
        """
        Validates and hashes a 4-digit numeric pin before saving.
        """
        if not raw_pin.isdigit() or len(raw_pin) != 4:
            raise ValidationError("Transaction PIN must be exactly 4 digits.")
        self.transaction_pin = make_password(raw_pin)

    def check_transaction_pin(self, raw_pin: str) -> bool:
        """
        Checks if the entered pin matches the stored hash.
        """
        return check_password(raw_pin, self.transaction_pin)

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Investment(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='invest/image', default='avatars/avatar.jpg', blank=True)
    min_amount = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True, null=True)
    max_amount = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True, null=True)
    daily_rate = models.FloatField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    period_in_days = models.IntegerField(blank=True, null=True)
    referral_commission = models.FloatField(blank=True, null=True)
    percentage = models.IntegerField(blank=True, null=True, default=100)

    def __str__(self):
        return str(self.name)


class Investment_profile(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='inv')
    trx_id = models.CharField(max_length=300, blank=True, null=True, )
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, null=True, blank=True)
    amount_invested = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True,
                                 null=True)
    amount_earned = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True,
                               null=True)
    expected_roi = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True, null=True)
    earning = MoneyField(max_digits=19, decimal_places=2, default_currency='USD', default=0, blank=True, null=True)
    status = models.CharField(max_length=300, blank=True, null=True, choices=investment_status)
    payout_frequency = models.CharField(max_length=300, choices=payout_frequency, blank=True, null=True)
    date_started = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    next_payout = models.DateTimeField(blank=True, null=True)
    expired = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)


class PaymentMethods(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_crypto = models.BooleanField(default=False)
    logo = models.ImageField(blank=True, null=True)
    for_deposit = models.BooleanField(default=False)
    transfer_access = models.BooleanField(default=False)
    for_withdrawal = models.BooleanField(default=False)
    wallet_address = models.CharField(max_length=300, blank=True, null=True)
    wallet_qrcode = models.ImageField(blank=True, null=True)
    deposit_transaction_message = models.TextField(blank=True, null=True)
    withdrawal_transaction_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.name)

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.wallet_address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_binary = buffer.getvalue()
        buffer.close()

        file_name = f"{self.name}.png"
        self.wallet_qrcode.save(file_name, ContentFile(image_binary), save=False)

    class Meta:
        verbose_name_plural = 'Payment Methods'

    def save(self, *args, **kwargs):
        self.generate_qr_code()
        super().save(*args, **kwargs)


class AdminWallet(models.Model):
    name = models.CharField(max_length=123, null=True)
    wallet_address = models.CharField(max_length=200, null=True)
    wallet_qr_code = models.ImageField(upload_to='admin_wallet/', blank=True, null=True)

    def __str__(self):
        return self.name

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.wallet_qr_code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_binary = buffer.getvalue()
        buffer.close()

        file_name = f"{self.name}.png"
        self.wallet_qr_code.save(file_name, ContentFile(image_binary), save=False)

    def save(self, *args, **kwargs):
        self.generate_qr_code()
        super().save(*args, **kwargs)



class KYC(models.Model):
    user = models.ForeignKey(Client, verbose_name=_("Client"), on_delete=models.CASCADE, related_name='kyc')
    first_name = models.CharField(_("First Name"), max_length=150)
    last_name = models.CharField(_("last Name"), max_length=150)
    dob = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=100, choices=GENDER_CHOICE, null=True)
    postcode = models.CharField(_("Postcode/Zipcode"), max_length=50)
    address = models.CharField(_("Address"), max_length=255)
    state = models.CharField(_("State"), max_length=150)
    document_type = models.CharField(max_length=50, choices=ID, null=True)
    id_front_view = models.FileField(upload_to="kyc/%Y-%m-%d/", null=True)
    id_back_view = models.FileField(upload_to="kyc/%Y-%m-%d/", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "KYC"
        verbose_name_plural = "KYCs"

    def __str__(self):
        return str(self.user)


class CompanyProfile(models.Model):
    name = models.CharField(max_length=225, blank=True, null=True)
    domain = models.URLField(max_length=200, blank=True, null=True)
    logo = models.ImageField(blank=True, null=True, upload_to='company/')
    favicon = models.ImageField(blank=True, null=True, upload_to='company/')
    support_email = models.EmailField(blank=True, null=True)
    forwarding_email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name