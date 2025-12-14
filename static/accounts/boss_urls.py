from django.urls import path

from accounts.boss_view import *
app_name = 'boss'

urlpatterns = [
    path('admin-dashboard', dashboard, name='admin-dashboard'),
    path('client-list', client_list, name='clients'),
    path('client-profile/<int:id>', client_profile, name='client_profile'),
    path('client-account/<int:id>', client_account, name='client_account'),
    path('client-investments/<int:id>', client_investment, name='client_investment'),
    path('client-kyc/<int:id>', client_kyc, name='client_kyc'),
    path('kyc-delete/<int:id>', kyc_delete, name='kyc_delete'),
    path('transactions', client_transactions, name='transactions'),
    path("wallets/", wallet_manager, name="wallet_manager"),
    path("wallets/<int:id>/delete/", wallet_delete, name="wallet_delete"),
    path('transaction/<int:id>', transaction_detail, name='transaction_detail'),
    path('client-delete/<int:id>', client_delete, name='client_delete' ),
    path('client-deactivate/<int:id>', client_deactivate, name='client_deactivate'),
    path('client-activate/<int:id>', client_activate, name='client_activate'),
    path('kyc-verify/<int:id>', kyc_verify, name='kyc_verify' )
]