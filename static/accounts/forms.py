from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from phonenumber_field.formfields import PhoneNumberField

from accounts.admin_form import FixedCountryField
from accounts.models import Client, KYC, Account, AdminWallet

User = get_user_model()
class UserRegistrationForm(UserCreationForm):
    phone_number = PhoneNumberField(
        region=None,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. +1728012345678",
                "class": "form-control h-56-px bg-neutral-50 radius-12",
            }
        ),
    )
    country = FixedCountryField(required=True, blank_label="Select Country",
        widget=forms.Select(attrs={"class": "form-control -neutral-50 radius-12"})  # no flags
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        if Client.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError(
                'Phone Number already exist'
            )

        return phone_number

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # skip uniqueness check entirely
        return username


class VerificationForm(forms.ModelForm):
    class Meta:
        model = KYC
        fields = ['first_name', 'last_name', 'dob', 'gender', 'postcode', 'address', 'id_front_view', 'document_type',
                  'state','id_back_view', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'form-control '

                )
            })



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name',  'Verification_status' ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'form-control '

                )
            })

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['main_balance']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'form-control '

                )
            })


class WalletForm(forms.ModelForm):
    class Meta:
        model = AdminWallet
        fields = ['name', 'wallet_address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet Name'}),
            'wallet_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet Address'}),
        }