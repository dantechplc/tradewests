from django.contrib import admin
from django.utils.html import format_html

from transaction.models import Transactions


# Register your models here.
@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = (
        "trx_id", "user", "amount", "status", "transaction_type",
        "date", "receipt_preview"
    )
    list_filter = ("status", "transaction_type", "date")
    search_fields = ("trx_id", "user__username", "wallet_address")
    readonly_fields = ("receipt_preview", )

    fieldsets = (
        ("Transaction Info", {
            "fields": ("user", "trx_id", "amount",  "status", "transaction_type", "date")
        }),
        ("Payment Details", {
            "fields": ("investment_name", "payment_methods", "wallet_address", "payment_description")
        }),
        ("Receipt", {
            "fields": ("receipt_upload", "receipt_preview")
        }),
    )

    def receipt_preview(self, obj):
        if obj.receipt_upload:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width:150px; height:auto; border:1px solid #ddd; border-radius:6px;"/>'
                '</a>',
                obj.receipt_upload.url,
                obj.receipt_upload.url
            )
        return "No Receipt"
    receipt_preview.short_description = "Receipt Preview"