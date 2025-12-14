

import djmoney
from django import forms
from djmoney.money import Money
from pkg_resources import require

from accounts.models import AdminWallet, Investment
from transaction.models import Transactions




class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = [
            'amount',
            'fees',
            'transaction_type',
            'payment_methods',
            'wallet_address',
            'status',
            'receipt_upload'

        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.user = self.account
        return super().save()

class DepositForm(TransactionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['payment_methods'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_deposit_amount = djmoney.money.Money(10, 'USD')

        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} '
            )

        return amount

class Payment_MethodForm(forms.Form):
    admin_wallet = AdminWallet.objects.all()
    payment_method = forms.ModelChoiceField(queryset=admin_wallet, required=True, empty_label='Select payment method')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update(
            {'class': 'col-lg-6  form-control', })



class InvestmentForm(TransactionForm):
    def __init__(self, *args, **kwargs):
        # self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    class Meta:
        model = Transactions
        fields = [
            'amount',
            'transaction_type',
            'investment_name',
        ]

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        investment_plan = Investment.objects.get(id=self.data['investment_name'])
        account = self.account
        min_amount = investment_plan.min_amount
        max_amount = investment_plan.max_amount
        balance = account.account.main_balance

        if amount < min_amount:
            raise forms.ValidationError(
                f'You can invest at least {min_amount}'
            )

        if amount > max_amount:
            raise forms.ValidationError(
                f'You can invest at most {max_amount} '
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your account. '
                'You can not invest more than you have in your account balance'
            )

        return amount




class WithdrawalForm(TransactionForm):
    wallet_address = forms.CharField(
        label="Wallet Address",
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "id": "wallet_address",
                "class": "form-control",
                "placeholder": "Enter your wallet address",
            }
        ),
    )
    def __init__(self, *args, **kwargs):
        # self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['payment_methods'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()

    class Meta:
        model = Transactions
        fields = [
            'amount',
            'transaction_type',
            'wallet_address',
            'payment_description',
            'payment_methods'

        ]

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        account = self.account
        min_amount = djmoney.money.Money(50, 'USD')
        balance = account.account.main_balance

        if amount < min_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_amount}'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your account. '
                'You can not withdraw more than you have in your account balance'
            )
        if account.Verification_status == 'Unverified':
            raise forms.ValidationError(
                f'Please Verify your Account !'
            )
        if account.Verification_status == 'Under Review':
            raise forms.ValidationError(
                f'Your Account is Under Review !')
        return amount





class ROIWithdrawalForm(TransactionForm):

    def __init__(self, *args, **kwargs):
        # self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['payment_methods'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()
        self.fields['status'].disabled = True
        self.fields['status'].widget = forms.HiddenInput()

    class Meta:
        model = Transactions
        fields = [
            'amount',
            'transaction_type',
            'payment_methods',
            'status'

        ]

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        account = self.account
        min_amount = djmoney.money.Money(50, 'USD')
        balance = account.account.roi_balance

        if amount < min_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_amount}'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your account. '
                'You can not withdraw more than you have in your ROI balance'
            )

        return amount


