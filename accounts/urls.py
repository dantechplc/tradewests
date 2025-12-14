from django.urls import path, include
from django.contrib.auth import views as auth_views


from accounts.views import *

app_name = 'accounts'

urlpatterns=[
    path('login', LoginView, name='login'),
    path('sign-up', SignupView, name='signup'),
    path('logout', logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),


     #
    path('reset_password/',
         CustomPasswordResetView.as_view(),
         name="reset_password"),
     path("reset_password_done/",
         auth_views.PasswordResetDoneView.as_view(template_name="accounts/auth/password_reset_done.html"),
         name="password_reset_done"),

    path("reset/<uidb64>/<token>/",
         CustomPasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),

    path(
        "reset_password_complete/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("account-profile", account_profile, name="account_profile"),
     path('change-password', change_password, name="change_password"),
      path('customer-support', customer_support, name="customer-support"),
    path('verification', verification, name='verify')
]

