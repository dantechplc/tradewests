from .views import *
from django.urls import path
app_name='transaction'

urlpatterns=[
    path('dashboard', dashboard, name="dashboard"),
    path('deposit/', Depositview, name='deposit'),
    path('deposit/<str:method>', DepositDetailView.as_view(), name='deposit-detail'),
    path('new-investment', investment, name='new-investment'),
    path('invest-preview/<str:investment_name>', InvestPreview.as_view(), name='investment_preview'),
    path('portfolio', Portfolio, name='portfolio'),
    path('investment-log', investment_log, name='investment-log'),
    path('Analysis', Analysis, name='analysis'),
    path('withdraw', withdraw_view, name='withdraw' ),
    path('withdraw/<str:method>', WithdrawMoneyView.as_view(), name='withdrawal_details'),
     path('roi-withdrawal', ROIWithdrawMoneyView.as_view(), name='roi-withdrawal'),
    path('transactions', transactions, name='transactions'),
    path('hx-search/', hx_search, name="hx-search"),
]