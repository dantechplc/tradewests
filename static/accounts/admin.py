from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from accounts.admin_form import ClientForm
from accounts.models import *


# Register your models here.

@admin.register(User)
class UserAdmin(UserAdmin):
    """Define admin model for custom User model with no username field."""
    fieldsets = (
        (_('password'), {'fields': ('password',)}),
        (_('Personal info'), {'fields': ('email', 'username', 'first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_client', 'is_superuser', 'is_staff',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'is_client', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)




class AccountInline(admin.StackedInline):
    model = Account



@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientForm   # ✅ apply patched form
    list_display = (
        "id", "user", "first_name", "last_name", "email",
        "phone_number", "country", "Verification_status",
        "date_joined", "recommended_by"
    )
    search_fields = (
        "user__username", "first_name", "last_name",
        "phone_number", "referral_code"
    )
    list_filter = (
        "Verification_status",
        "gender",
        "date_joined",
    )
    readonly_fields = ("referral_code",)
    autocomplete_fields = ("recommended_by", "user")
    inlines = [AccountInline]

    def email(self, obj):
        return obj.user.email if obj.user else "-"
    email.short_description = "Email"


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "main_balance", "book_balance", "bonus",
        "total_amount_deposited", "total_amount_withdrawn",
        "roi_balance", "balance_status",
        "last_deposit_date", "last_withdrawal_date"
    )
    search_fields = (
        "user__user__username",
        "user__first_name",
        "user__last_name"
    )
    list_filter = ("balance_status",)
    autocomplete_fields = ("user",)


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        "name", "min_amount", "max_amount",
        "daily_rate", "duration", "period_in_days",
        "referral_commission", "percentage",
    )
    search_fields = ("name",)
    list_filter = ("duration", "period_in_days")
    readonly_fields = ()
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "image")
        }),
        ("Investment Limits", {
            "fields": ("min_amount", "max_amount", "percentage")
        }),
        ("Rates & Duration", {
            "fields": ("daily_rate", "duration", "period_in_days", "referral_commission")
        }),
    )


@admin.register(Investment_profile)
class InvestmentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "investment", "trx_id", "amount_invested",
        "amount_earned", "expected_roi", "status",
        "payout_frequency", "date_started", "expiry_date", "expired",
    )
    search_fields = ("user__email", "trx_id", "investment__name")
    list_filter = ("status", "payout_frequency", "expired", "date_started")
    #readonly_fields = ("amount_earned", "earning")  # example: if you want these not editable
    fieldsets = (
        ("User & Investment", {
            "fields": ("user", "trx_id", "investment", "status", "payout_frequency")
        }),
        ("Financials", {
            "fields": ("amount_invested", "amount_earned", "expected_roi", "earning")
        }),
        ("Dates", {
            "fields": ("date_started", "expiry_date", "next_payout", "expired")
        }),
    )


@admin.register(PaymentMethods)
class PaymentMethodsAdmin(admin.ModelAdmin):
    list_display = (
        "name", "is_active", "is_crypto", "for_deposit",
        "for_withdrawal", "transfer_access",
    )
    search_fields = ("name", "wallet_address")
    list_filter = ("is_active", "is_crypto", "for_deposit", "for_withdrawal", "transfer_access")
    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "logo", "is_active", "is_crypto")
        }),
        ("Usage", {
            "fields": ("for_deposit", "for_withdrawal", "transfer_access")
        }),
        ("Wallet", {
            "fields": ("wallet_address", "wallet_qrcode", "transaction_fee")
        }),
        ("Messages", {
            "fields": ("deposit_transaction_message", "withdrawal_transaction_message")
        }),
    )


from django.contrib import admin
from .models import AdminWallet

@admin.register(AdminWallet)
class AdminWalletAdmin(admin.ModelAdmin):
    list_display = ('name', 'wallet_address', 'wallet_qr_code_display')
    search_fields = ('name', 'wallet_address')


    # Optional: show QR code image in admin
    def wallet_qr_code_display(self, obj):
        if obj.wallet_qr_code:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.wallet_qr_code.url)
        return "-"
    wallet_qr_code_display.short_description = "QR Code"


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "dob",
        "gender",
        "state",
        "document_type",
        "created"

    )
    search_fields = (
        "first_name",
        "last_name",
        "user__email",
        "user__username",
        "postcode",
        "state",
    )
    list_filter = ("gender", "document_type", "state")
    ordering = ("-created",)
    readonly_fields = ("id_front_preview", "id_back_preview", 'created')

    fieldsets = (
        ("Client Info", {
            "fields": ("user", "first_name", "last_name", "dob", "gender",),
        }),
        ("Address Info", {
            "fields": ("address", "state", "postcode"),
        }),
        ("Verification Document", {
            "fields": ("document_type", "id_front_view", "id_front_preview", "id_back_view", "id_back_preview"),
        }),
    )

    def id_front_preview(self, obj):
        if obj.id_front_view:
            return f'<a href="{obj.id_front_view.url}" target="_blank">📄 View Front</a>'
        return "No document"
    id_front_preview.allow_tags = True
    id_front_preview.short_description = "ID Front Preview"

    def id_back_preview(self, obj):
        if obj.id_back_view:
            return f'<a href="{obj.id_back_view.url}" target="_blank">📄 View Back</a>'
        return "No document"
    id_back_preview.allow_tags = True
    id_back_preview.short_description = "ID Back Preview"



@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "support_email", "phone", "logo_preview", "favicon_preview")
    search_fields = ("name", "domain", "support_email", "forwarding_email", "address", "phone")
    list_filter = ("support_email",)

    fieldsets = (
        ("Company Info", {
            "fields": ("name", "domain", "address", "phone")
        }),
        ("Branding", {
            "fields": ("logo", "favicon")
        }),
        ("Support & Contact", {
            "fields": ("support_email", "forwarding_email")
        }),
    )

    readonly_fields = ("logo_preview", "favicon_preview")

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.logo.url)
        return "—"
    logo_preview.short_description = "Logo"

    def favicon_preview(self, obj):
        if obj.favicon:
            return format_html('<img src="{}" style="max-height:30px;"/>', obj.favicon.url)
        return "—"
    favicon_preview.short_description = "Favicon"