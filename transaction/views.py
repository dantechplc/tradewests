import datetime

import djmoney
import sweetify
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView

from accounts.decorators import allowed_users
from accounts.models import AdminWallet, Investment, Investment_profile, Account, CompanyProfile, InvestmentCategory
from transaction import EmailSender
from transaction.constants import TRANSACTION_TYPE_CHOICES
from transaction.forms import DepositForm, Payment_MethodForm, InvestmentForm, WithdrawalForm, ROIWithdrawalForm
from transaction.models import Transactions


# Create your views here.


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def dashboard(request):
    promo_id = request.session.pop('promo_investment_id', None)
    promo_investment = None
    if promo_id:
        promo_investment = Investment.objects.filter(id=promo_id).prefetch_related('benefits').first()


    latest_transactions = Transactions.objects.filter(user=request.user.client)[::-1]

    context = {

        'navbar': "home",
        "promo_investment": promo_investment,
        'transactions': latest_transactions[:5]
    }

    return render(request, 'transaction/dsh/dashboard/dashboard.html', context)


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    model = Transactions

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.client
        })
        return kwargs

    @method_decorator(allowed_users(allowed_roles=['clients']))
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)




class DepositDetailView(TransactionCreateMixin):
    template_name = 'transaction/dsh/dashboard/deposit_detail.html'
    form_class = DepositForm
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        method = kwargs['method']
        self.payment_method = method
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        initial = {'transaction_type': "DEPOSIT",
                   'payment_methods': AdminWallet.objects.get(id=self.payment_method),
                   }
        return initial

    def form_valid(self, form, *args, **kwargs):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = AdminWallet.objects.get(id=self.payment_method)

        # send deposit request email to admin
        email_address = CompanyProfile.objects.first().forwarding_email  # support email

        EmailSender.deposit_request_email(email_address=email_address, amount=amount,
                                          client=account,
                                         payment_method=payment_method)
        # get transaction message from payment method
        message = f"Your {payment_method} deposit request is being processed! "
        sweetify.success(self.request, 'Success!', text=f'{message}', button='OK', timer=10000,
                         timerProgressBar='true')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(AdminWallet, id=self.payment_method)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "deposit",
            'method': payment_method,
        })
        return context


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def Depositview(request):
    form = Payment_MethodForm(request.POST)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        return redirect('transaction:deposit-detail', payment_method)

    context = {
        'navbar': 'deposit',
        'form':form
    }
    return render(request, 'transaction/dsh/dashboard/deposit_method.html', context)



@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def investment(request):
    categories = InvestmentCategory.objects.all()
    investments = Investment.objects.filter(is_active=True).select_related("category").prefetch_related("benefits")

    context = {
        'investments': investments,
        'navbar': 'investment',
        "categories": categories
    }
    if request.method == 'POST':
        investment_name = request.POST.get('investment_name')
        return redirect('transaction:investment_preview', investment_name)

    return render(request, "transaction/dsh/dashboard/new_investment.html", context)





class InvestPreview(TransactionCreateMixin):
    success_url = reverse_lazy('transaction:transactions')
    form_class = InvestmentForm
    title = 'Investment'
    template_name = 'transaction/dsh/dashboard/investment_preview.html'

    def get_initial(self):
        initial = {'transaction_type': "INVESTMENT"}
        return initial

    def form_valid(self, form):
        account = self.request.user
        investment_id = form.cleaned_data.get('investment_name')
        investment_name = Investment.objects.get(name=investment_id)
        amount = form.cleaned_data.get('amount', 'USD')
        investment_acct_name = Investment.objects.get(name=investment_name)
        usd_balance = Account.objects.get(user=self.request.user.client)



        roi = Transactions.ROI(amount=amount, rate=investment_acct_name.daily_rate,
                              days=investment_acct_name.period_in_days)
        usd_balance.main_balance -= form.cleaned_data.get('amount')
        usd_balance.total_amount_investment += form.cleaned_data.get('amount')
        usd_balance.total_expected_roi += roi
        usd_balance.save(
            update_fields=['main_balance', 'total_amount_investment', 'total_expected_roi' ])

        earning = Transactions.earning(amount=amount, rate=investment_acct_name.daily_rate)
        sa = form.save(commit=False) # form object
        sa.status = "Successful"
        sa.investment_name = Investment.objects.get(name=str(self.investment_name))
        sa.save()

        # investment_profile_creation
        client_investment = Investment_profile.objects.create(
            user=self.request.user.client,
            investment=Investment.objects.get(name=investment_acct_name),
            amount_invested=amount,
            expected_roi=roi,
            earning=earning,
            status='Active',
            trx_id=sa.pk,
            date_started=timezone.now(),
            expiry_date= Transactions.add_business_days(timezone.now(), investment_acct_name.period_in_days),
            next_payout=Transactions.get_next_payout(timezone.now()),
        )
        client_investment.save()
        sweetify.success(self.request, 'Success!', text=f'Your {investment_name} successfully created !', button='OK',
                             timer=10000,
                             timerProgressBar='true')

        EmailSender.InvestmentSuccess(email=str(self.request.user),
                                      name=self.request.user.username,
                                      balance=usd_balance.main_balance,
                                      investment=client_investment.investment, amount=amount,
                                      expected_roi=client_investment.expected_roi,
                                      next_payout=client_investment.next_payout,
                                      trx_id = sa.trx_id,
                                      earning=client_investment.earning, date=client_investment.date_started)

        return super(InvestPreview, self).form_valid(form)

    def setup(self, request, *args, **kwargs):
        self.investment_name = kwargs['investment_name']
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        investment = Investment.objects.get(name=str(self.investment_name))
        context = super().get_context_data(**kwargs)

        context.update({
            'account': self.request.user,
            'time': datetime.datetime.now(),
            'investment': investment,
            'navbar': 'investment'
        })

        return context

import random
from django.shortcuts import render

import json
from django.utils.safestring import mark_safe
from djmoney.money import Money
@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def Portfolio(request):
    user = request.user.client

    # Get all active investments
    active_transactions = Investment_profile.objects.filter(
        user=user,
        status="Active",
    )

    labels = []
    earnings = []
    colors = []
    investments_data = []
    expected_roi = []

    # Predefined palette
    palette = [
        "#4CAF50", "#2196F3", "#FFC107", "#9C27B0",
        "#FF5722", "#00BCD4", "#8BC34A", "#E91E63",
        "#3F51B5", "#009688"
    ]

    for i, trx in enumerate(active_transactions):
        plan_name = str(trx.investment) if trx.investment else "Unknown Plan"
        earned = trx.amount_earned or Money(0, "USD")
        invested = trx.amount_invested or Money(0, "USD")
        expected_return = trx.expected_roi or Money(0, "USD")

        # Progress calculation
        progress = 0
        if expected_return.amount > 0:
            progress = round((earned.amount / expected_return.amount) * 100, 2)
            progress = min(progress, 100)

        # Chart arrays
        labels.append(plan_name)
        earnings.append(float(earned.amount))
        expected_roi.append(float(trx.expected_roi.amount))
        colors.append(palette[i % len(palette)])

        # Card data
        investments_data.append({
            "plan": plan_name,
            "amount": invested,
            "earned": earned,
            'expected_roi': trx.expected_roi,
            "status": trx.status,
            "progress": progress,
        })

    # Portfolio summary
    account = Account.objects.get(user=user)

    context = {
        "labels": mark_safe(json.dumps(labels)),
        "earnings": mark_safe(json.dumps(earnings)),
        "colors": mark_safe(json.dumps(colors)),
        "investments": investments_data,
        "expected_roi": expected_roi,
        "total_invested": account.total_amount_investment,
        "total_earnings": account.total_roi_received,
        "total_plans": active_transactions.count(),
        'navbar': 'investment'
    }
    return render(request, 'transaction/dsh/dashboard/portfolio.html', context)


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def investment_log(request):
    account = request.user.client
    transactions = Investment_profile.objects.filter(user=account)[::-1]
    transaction = []
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 10)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    for x in transactions:
        transaction.append(x)

    context = {'transaction': transaction,
               'users': users,
               'navbar': 'investment'
               }
    return render(request, 'transaction/dsh/dashboard/investment_log.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def Analysis(request):
    context = {
        'navbar':'analysis'
    }
    return  render(request,'transaction/dsh/dashboard/market.html', context )

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def withdraw_view(request):
    payment_method = AdminWallet.objects.all()
    if request.method == 'POST':
            payment_method = request.POST.get('payment_method')
            method = get_object_or_404(AdminWallet, name=payment_method)
            return redirect('transaction:withdrawal_details', method=method,)
    context = {
        'payment_method':payment_method,
        'navbar': 'withdrawal'
    }
    return render(request, 'transaction/dsh/dashboard/withdraw.html', context )



class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawalForm
    template_name = 'transaction/dsh/dashboard/crypto_withdrawal.html'
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = AdminWallet.objects.get(name=self.payment_method)
        initial = {'transaction_type': "WITHDRAWAL",
                   'payment_methods': payment_method,
                   }
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')


        # send withdrawal request email to admin
        email_address = CompanyProfile.objects.first().forwarding_email  # support email
        EmailSender.withdrawal_request_email(email_address=email_address, amount=amount, client=account,
                                             payment_method=payment_method)
        message = 'Your withdrawal request is being processed!'
        sweetify.success(self.request, 'Success!', text=f'{message}', button='OK', timer=10000,
                         timerProgressBar='true')

        form.save(commit=True)

        return super(WithdrawMoneyView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(AdminWallet, name=self.payment_method)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "withdrawal",
            'method': payment_method,
        })
        return context


class ROIWithdrawMoneyView(TransactionCreateMixin):
    form_class = ROIWithdrawalForm
    template_name = 'transaction/dsh/dashboard/roi_withdrawal.html'
    success_url = reverse_lazy('transaction:transactions')

    def get_initial(self):

        initial = {'transaction_type': "WITHDRAW",
                   'payment_methods': 'ROI',
                   'status': 'Successful'
                   }
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')


        # Deduct from ROI balance and Credit the main balance
        account = Account.objects.get(user=self.request.user.client)
        account.roi_balance -= amount
        account.main_balance += amount
        account.save(update_fields=['main_balance', 'roi_balance'])

        message = 'Your ROI withdrawal has been credited to your main balance'
        sweetify.success(self.request, 'Success!', text=f'{message}', button='OK', timer=10000,
                         timerProgressBar='true')

        form.save(commit=True)

        return super(ROIWithdrawMoneyView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "withdrawal",

        })
        return context


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def transactions(request):
    account = request.user.client
    trans = Transactions.objects.filter(user=account)[::-1]
    trans_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(trans, 10)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    for x in trans:
        trans_list.append(x)

    transaction = trans_list

    context = {'transaction': transaction,
               'transactions': users,
               'navbar': "transactions",

               }

    return render(request, 'transaction/dsh/dashboard/transactions.html', context)


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def hx_search(request):
    account = request.user.client
    query = request.GET.get('q')
    if query:
        try:
            query_int = int(query)
        except ValueError:
            # if the query is not a valid integer, try to find the corresponding transaction type by name
            query_int = next((value for value, name in TRANSACTION_TYPE_CHOICES if name.lower() == query.lower()), None)
            if query_int is None:
                # if the transaction type name is not found, return an empty results
                results = Transactions.objects.filter(
                    Q(amount__icontains=query) |
                    Q(date__icontains=query) |
                    Q(trx_id=query) |
                    Q(status__icontains=query), user=account,
                )[::-1]
            else:
                results = Transactions.objects.filter(
                    Q(amount__icontains=query) |
                    Q(transaction_type=query_int) |
                    Q(date__icontains=query) |
                    Q(trx_id=query) |
                    Q(status__icontains=query), user=account,
                )[::-1]
        else:
            results = Transactions.objects.filter(
                Q(amount__icontains=query) |
                Q(transaction_type=query_int) |
                Q(date__icontains=query) |
                Q(trx_id=query) |
                Q(status__icontains=query), user=account,
            )[::-1]

    else:
        results = Transactions.objects.filter(user=account)[::-1]

    return render(request, 'transaction/dsh/dashboard/partials/transactions.html',
                  {'transactions': results, 'navbar': 'transactions'})
