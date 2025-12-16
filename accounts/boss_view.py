from datetime import timedelta
from decimal import Decimal

import sweetify
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from djmoney.money import Money

from accounts import EmailSender
from accounts.decorators import allowed_users
from accounts.forms import ProfileForm, AccountForm, WalletForm, VerificationForm
from accounts.models import Client, KYC, Investment_profile, AdminWallet, Account
from transaction.models import Transactions

User = get_user_model()


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def dashboard(request):
     # Example stats - replace with real queries
    total_clients = Client.objects.count()
    pending_withdrawals_total = Transactions.objects.filter(status="pending", transaction_type='WITHDRAW').count()
    pending_deposits_total = Transactions.objects.filter(status="pending", transaction_type='DEPOSIT').count()

    # KYC status counts (assuming a model field like `status`)
    kyc_completed = Client.objects.filter(Verification_status="Verified").count()
    kyc_under_review = Client.objects.filter(Verification_status="Under Review").count()
    kyc_unverified = Client.objects.filter(Verification_status="Unverified").count()

    # Recent data
    # Get the latest withdrawals
    recent_withdrawals = Transactions.objects.filter(transaction_type='WITHDRAWAL').order_by('-date')  # newest first

    # Get the latest deposits
    recent_payments = Transactions.objects.filter(transaction_type='DEPOSIT').order_by('-date')  # newest first

    # Optionally, limit to last N transactions, e.g., last 5
    recent_withdrawals = recent_withdrawals[:5]
    recent_payments = recent_payments[:5]
    recent_clients = Client.objects.order_by('-date_joined')[:5]  # get latest 5
    #recent_client = reversed(recent_clients)  # display oldest first


    context = {
        "total_clients": total_clients,
        "pending_withdrawals_total": pending_withdrawals_total,
        "pending_deposits_total": pending_deposits_total,
        "kyc_completed": kyc_completed,
        "kyc_under_review": kyc_under_review,
        "kyc_unverified": kyc_unverified,
        "recent_withdrawals": recent_withdrawals,
        "recent_payments": recent_payments,
        "recent_clients": recent_clients,
        'navbar':'dashboard',
    }
    return render(request, 'accounts/boss/dashboard.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_list(request):
    query = request.GET.get('q', '')
    clients = Client.objects.all().order_by('-user__date_joined')  # latest first
    page = request.GET.get('page', 1)
    if query:
        clients = clients.filter(
            Q(user__first_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(country__icontains=query)
        )


    paginator = Paginator(clients, 10)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    context ={
        'clients':clients,
        'users':users,
        'navbar': 'clients',
        'request': request
    }
    return render(request, 'accounts/boss/client_list.html', context)


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_profile(request, id):
    client = get_object_or_404(Client, id=id)
    status = client.Verification_status

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=client)
        if form.is_valid():
            try:
                # Save client instance with new data
                client_instance = form.save(commit=False)

                # Update User model username
                user = User.objects.get(email=client.user.email)
                user.username = request.POST.get('first_name')
                user.save(update_fields=['username'])

                # Check if status changed to Verified
                new_status = client_instance.Verification_status
                client_instance.save()

                if status != 'Verified' and new_status == 'Verified':
                    EmailSender.kyc_verified(email=client.user.email, name=client.first_name)

                sweetify.success(
                    request,
                    'Success!',
                    text='Data updated successfully!',
                    button='OK',
                    timer=10000,
                    timerProgressBar=True
                )
                return redirect('boss:client_profile', id=id)

            except Exception as e:
                sweetify.error(
                    request,
                    'Update failed!',
                    text=str(e),
                    button='OK',
                    timer=8000,
                    timerProgressBar=True
                )
        else:
            # show error popup if validation fails
            sweetify.error(
                request,
                'Invalid data!',
                text='Please check the highlighted fields.',
                button='OK',
                timer=8000,
                timerProgressBar=True
            )
    else:
        form = ProfileForm(instance=client)

    context = {
        'client': client,
        'nav': 'profile',
        'form': form,
        'navbar': 'clients'
    }
    return render(request, 'accounts/boss/client_profile.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_account(request, id):
    client = get_object_or_404(Client, id=id)

    if request.method == "POST":
        form = AccountForm(request.POST, instance=client.account)
        if form.is_valid():
            form.save()
            sweetify.success(
                request,
                'Success!',
                text='Data updated successfully!',
                button='OK',
                timer=10000,
                timerProgressBar=True
            )
            return redirect('boss:client_account', id=id)
        else:
            # Form is invalid — render the same template with errors
            sweetify.error(
                request,
                'Error!',
                text='Please correct the errors below.',
                button='OK',
                timer=10000,
                timerProgressBar=True
            )
    else:
        form = AccountForm(instance=client)  # Use AccountForm here too

    context = {
        'client': client,
        'nav': 'account',
        'form': form,
        'navbar': 'clients'
    }
    return render(request, 'accounts/boss/client_account.html', context)



@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_investment(request, id):
    client = get_object_or_404(Client, id=id)
     # Make sure we only fetch this client's investments
    investments = Investment_profile.objects.filter(user=client)[::-1]
    context = {
        'client': client,
        'nav': 'investment',
        'navbar': 'clients',
        'investments': investments,
    }
    return  render(request, 'accounts/boss/client_investment.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_kyc(request, id):
    client = get_object_or_404(Client, id=id)
     # Make sure we only fetch this client's investments
    kyc = KYC.objects.filter(user=client)[::-1]
    context = {
        'client': client,
        'nav': 'kyc',
        'navbar': 'clients',
        'kyc': kyc
    }
    return  render(request, 'accounts/boss/client_kyc.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_transactions(request):
    if request.method == "POST":
        tx_id = request.POST.get("transaction_id")
        action = request.POST.get("action")  # confirm / decline / delete
        transaction = get_object_or_404(Transactions, id=tx_id)

        if action == "confirm":
            if transaction.status == "pending" and transaction.transaction_type == "DEPOSIT":
                transaction.status = "Successful"
                transaction.save()
                account = Account.objects.get(user=transaction.user)
                account.main_balance += transaction.amount
                account.save(update_fields=['main_balance'])
                EmailSender.deposit_success(amount=transaction.amount, trx_id=transaction.trx_id,
                                           name=transaction.user.first_name, email=transaction.user,
                                           date=transaction.date, balance=account.main_balance)
                sweetify.success(request, f'{transaction.amount} deposit confirmed!')
                if not account.first_deposit:
                    try:
                        referral = transaction.user.recommended_by
                        if referral:
                            referral_account = Account.objects.get(user=referral)
                            bonus = Money(
                                    transaction.amount.amount * Decimal("0.10"),
                                    transaction.amount.currency
                                )
                            referral_account.main_balance += bonus
                            referral_account.save(update_fields=['main_balance'])
                            account = Account.objects.get(user=transaction.user)
                            account.first_deposit = True
                            account.save(update_fields=['first_deposit'])
                            subject = "🎉 Referral Bonus Earned!"
                            message = f"""
                            Dear {referral.first_name},
                
                            Congratulations! 🎉 you have earned {bonus} from your referral commission.
                
                            Please contact support if you need assistance.
                            Available balance: {referral_account.main_balance}
                
                            Thank you,
                            Tradewests Admin
                            """
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [referral.user])
                    except Client.DoesNotExist:
                        pass

                return redirect('boss:transactions')
            elif transaction.status == "pending" and transaction.transaction_type == "WITHDRAWAL":
                transaction.status = 'Successful'
                transaction.save()
                account = Account.objects.get(user=transaction.user)
                account.main_balance -= transaction.amount
                account.save(update_fields=['main_balance'])
                EmailSender.withdraw_success(amount=transaction.amount, trx_id=transaction.trx_id,
                                           name=transaction.user.first_name, email=transaction.user,
                                           date=transaction.date, balance=account.main_balance)
                sweetify.success(request, f'{transaction.amount} withdrawal confirmed!')
                return redirect('boss:transactions')

        elif action == "decline":
            transaction.status = "failed"
            transaction.save()
            account = Account.objects.get(user=transaction.user)

            subject = f"{transaction.transaction_type.capitalize()} Declined"
            message = f"""
            Dear {transaction.user.first_name},

            Unfortunately, your {transaction.transaction_type.lower()} of {transaction.amount} has been declined.

            Please contact support if you need assistance.
            Available balance: {account.main_balance}

            Thank you,
            Tradewests Admin
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.user])
            sweetify.success(request, f'{transaction.amount} {transaction.transaction_type.lower()}  decline confirmed!')

        elif action == "delete":
            transaction.delete()
            sweetify.success(request, f'{transaction.amount} {transaction.transaction_type.lower()}  delete confirmed!')


        return redirect("boss:transactions")

    tx_list = Transactions.objects.filter(
            transaction_type__in=["DEPOSIT", "WITHDRAWAL"]
        ).order_by("-id")  # latest first

    q = request.GET.get('q', '')  # get the search query

    if q:
        tx_list = tx_list.filter(
                Q(user__first_name__icontains=q) |
                Q(transaction_type__icontains=q) |
                Q(status__icontains=q) |
                Q(trx_id__icontains=q) |
                Q(amount__icontains=q) |
                Q(date__icontains=q)
            )

    paginator = Paginator(tx_list, 5)  # 5 per page
    page_number = request.GET.get("page")
    transactions = paginator.get_page(page_number)

    context = {
            'transactions': transactions,
            'navbar': 'transactions',
            'q': q,  # send back the search term
        }
    return render(request, "accounts/boss/transactions.html", context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def wallet_manager(request):
    wallets = AdminWallet.objects.all().order_by("-id")

    if request.method == "POST":
        if "wallet_id" in request.POST:  # Editing existing
            wallet = get_object_or_404(AdminWallet, id=request.POST["wallet_id"])
            form = WalletForm(request.POST, instance=wallet)
        else:  # Creating new
            form = WalletForm(request.POST)

        if form.is_valid():
            form.save()
            sweetify.success(request, 'Data updated')
            return redirect("boss:wallet_manager")
    else:
        form = WalletForm()

    return render(request, "accounts/boss/wallet_manager.html", {"wallets": wallets, "form": form, 'navbar':'wallet'})



@csrf_exempt
def wallet_delete(request, id):
    wallet = get_object_or_404(AdminWallet, id=id)
    if request.method == "POST":
        wallet.delete()
        sweetify.success(request, "Wallet deleted successfully ❌")
        return redirect("boss:wallet_manager")
    sweetify.error(request, "Invalid request")
    return redirect("boss:wallet_manager")

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def transaction_detail(request, id):
    # Only get transactions with type DEPOSIT or WITHDRAWAL
    transaction = get_object_or_404(
        Transactions,
        pk=id,
        transaction_type__in=["DEPOSIT", "WITHDRAWAL"]
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "confirm":
            if transaction.status == "pending" and transaction.transaction_type == "DEPOSIT":
                transaction.status = "Successful"
                transaction.save()
                account = Account.objects.get(user=transaction.user)
                account.main_balance += transaction.amount
                account.total_amount_deposited += transaction.amount
                account.save(update_fields=['main_balance', 'total_amount_deposited'])
                EmailSender.deposit_success(amount=transaction.amount, trx_id=transaction.trx_id,
                                           name=transaction.user.first_name, email=transaction.user,
                                           date=transaction.date, balance=account.main_balance)
                sweetify.success(request, f'{transaction.amount} deposit confirmed!')
                if not account.first_deposit:
                    try:
                        referral = transaction.user.recommended_by
                        if referral:
                            referral_account = Account.objects.get(user=referral)
                            bonus = Money(
                                    transaction.amount.amount * Decimal("0.10"),
                                    transaction.amount.currency
                                )
                            referral_account.main_balance += bonus
                            referral_account.save(update_fields=['main_balance'])
                            account = Account.objects.get(user=transaction.user)
                            account.first_deposit = True
                            account.save(update_fields=['first_deposit'])
                            subject = "🎉 Referral Bonus Earned!"
                            message = f"""
                            Dear {referral.first_name},
                
                            Congratulations! 🎉 you have earned {bonus} from your referral commission.
                
                            Please contact support if you need assistance.
                            Available balance: {referral_account.main_balance}
                
                            Thank you,
                            Tradewests Admin
                            """
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [referral.user])
                    except Client.DoesNotExist:
                        pass

                return redirect('boss:transactions')
            elif transaction.status == "pending" and transaction.transaction_type == "WITHDRAWAL":
                transaction.status = 'Successful'
                transaction.save()
                account = Account.objects.get(user=transaction.user)
                account.main_balance -= transaction.amount
                account.total_amount_withdrawn += transaction.amount
                account.save(update_fields=['main_balance', 'total_amount_withdrawn'])
                EmailSender.withdraw_success(amount=transaction.amount, trx_id=transaction.trx_id,
                                           name=transaction.user.first_name, email=transaction.user,
                                           date=transaction.date, balance=account.main_balance)
                sweetify.success(request, f'{transaction.amount} withdrawal confirmed!')
                return redirect('boss:transactions')

        elif action == "decline":
            transaction.status = "failed"
            transaction.save()
            account = Account.objects.get(user=transaction.user)

            subject = f"{transaction.transaction_type.capitalize()} Declined"
            message = f"""
            Dear {transaction.user.first_name},

            Unfortunately, your {transaction.transaction_type.lower()} of {transaction.amount} has been declined.

            Please contact support if you need assistance.
            Available balance: {account.main_balance}

            Thank you,
            Tradewests Admin
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.user])
            sweetify.success(request, f'{transaction.amount} {transaction.transaction_type.lower()}  decline confirmed!')

        elif action == "delete":
            transaction.delete()
            sweetify.success(request, f'{transaction.amount} {transaction.transaction_type.lower()}  delete confirmed!')


        return redirect("boss:transactions")  # Redirect to transaction list

    context = {
        "transaction": transaction,
        'navbar': 'transactions',
    }
    return render(request, "accounts/boss/transaction_detail.html", context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_delete(request, id):
    client = get_object_or_404(Client, pk=id)
    if client:
        # Get the associated user instance
        user = client.user
        user.delete()  # delete the user instance
        client.delete()  # delete the client instance
        sweetify.success(request, f'Client with email {user.email} deleted!')
    return redirect('boss:clients')

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_deactivate(request, id):
    client = get_object_or_404(Client, pk=id)
    if client:
        user = User.objects.get(email=str(client.user))
        user.is_active = False
        user.save(update_fields=['is_active'])
        sweetify.success(request, f'Client with email {client} is deactivated !')
    return redirect('boss:clients')

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def client_activate(request, id):
    client = get_object_or_404(Client, pk=id)
    if client:
        user = User.objects.get(email=str(client.user))
        user.is_active = True
        user.save(update_fields=['is_active'])
        sweetify.success(request, f'Client with email {client}  activated !')
    return redirect('boss:clients')

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def kyc_delete(request, id):
    kyc = get_object_or_404(KYC, pk=id)
    if kyc:
        kyc.delete()  # delete the client kyc instance
        sweetify.success(request, f'Client with email {kyc.user} KYC has been deleted!')
    return redirect('boss:client_profile', kyc.user.id)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['admin'])
@never_cache
def kyc_verify(request, id):
    kyc = get_object_or_404(KYC, pk=id)
    status = Client.objects.get(user=kyc.user.user)
    verify_stat =  status.Verification_status
    if request.method == "POST":
        client = Client.objects.get(user=kyc.user.user)
        client.Verification_status = "Verified"
        client.last_name = kyc.last_name
        client.gender = kyc.gender
        client.dob =kyc.dob
        client.address =kyc.address
        client.state = kyc.state
        client.zip = kyc.postcode
        client.save(update_fields=['last_name', 'Verification_status', 'gender', 'dob', 'address', 'state', 'zip'])
        if verify_stat != 'Verified':
            EmailSender.kyc_verified(email=client.user.email, name=client.first_name)
            sweetify.success(request, f'{client.first_name} account is now verified and notification email sent.')
        else:
            sweetify.info(request, f'{client.first_name} account is already verified')

    return redirect('boss:client_profile', kyc.user.id)

