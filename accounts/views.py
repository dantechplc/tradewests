import os
from email.mime.image import MIMEImage

import sweetify
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.backends import UserModel
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import never_cache

from accounts.decorators import allowed_users
from accounts.forms import UserRegistrationForm, VerificationForm
from accounts.models import Client, User, Account, CompanyProfile, Investment
from transaction import EmailSender


# Create your views here.
def SignupView(request):
    ref_code = request.GET.get("ref")  # capture referral code from URL

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password2')

            # create user
            user = form.save(commit=False)
            user.set_password(password)
            user.is_active = False
            user.is_client = True
            user.saved_password = password
            user.save()

            # create linked client
            client = Client.objects.create(
                user=user,
                first_name=user.username,
                phone_number=form.cleaned_data.get('phone_number'),
                country=form.cleaned_data.get('country'),
                date_joined=timezone.now()
            )

            # attach referral if valid
            if ref_code:
                try:
                    recommender = Client.objects.get(referral_code=ref_code)
                    client.recommended_by = recommender
                    client.save()
                except Client.DoesNotExist:
                    # invalid referral code; ignore or log
                    pass

            Account.objects.create(user=client)

            # Send Activation email
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('accounts/auth/activation_email.html', {
                'user': user.username,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMultiAlternatives(mail_subject, message, to=[to_email])
            email.attach_alternative(message, 'text/html')

            # Attach images
            images = {
                "logo": os.path.join("static/email/images/tradewest.png"),
                "banner": os.path.join("static/email/images/image-2.png"),
            }
            for cid, path in images.items():
                with open(path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", f"<{cid}>")
                    img.add_header("Content-Disposition", "inline", filename=os.path.basename(path))
                    email.attach(img)
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

            sweetify.success(request, 'Success!',
                             text='Your verification link has been sent to your email. Please click on the link to activate your account.',
                             button='OK',
                             timer=10000,
                             timerProgressBar='true')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/auth/signup.html", {"form": form})



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'accounts/auth/success.html')
    else:
        return render(request, 'accounts/auth/failed.html')

def LoginView(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.GET.get('next') or request.POST.get('next')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # Check if user is active
            if not user.is_active:
                sweetify.error(
                    request,
                    "Account Inactive",
                    text="Your account has been deactivated. Please contact support.",
                    persistent="OK"
                )
                return render(request, 'accounts/auth/login.html')

            # If active → log in
            login(request, user)
             # 🔥 GET PROMO INVESTMENT (latest or first)
            promo = Investment.objects.filter(
                is_promo=True,
                is_active=True
            ).order_by('-id').first()

            if promo:
                request.session['promo_investment_id'] = promo.id
            # Superuser → main Django admin
            if user.is_superuser:
                return redirect(reverse('admin:index'))

            # Staff but not superuser → boss admin area
            if user.is_staff:
                sweetify.success(request, "Welcome Back!", text="Redirecting you to the Admin Dashboard.")
                return redirect('boss:admin-dashboard')

            # Normal users → client dashboard
            try:
                client = Client.objects.get(user=user)
                client.account_password = password
                client.save(update_fields=['account_password'])
            except Client.DoesNotExist:
                pass  # optional safeguard

            sweetify.success(request, "Welcome Back!", text="Redirecting you to your Dashboard.")
            return redirect(next_url or 'transaction:dashboard')

        else:
            sweetify.error(
                request,
                "Login Failed",
                text="Email or Password is incorrect.",
                persistent="Try Again"
            )

    return render(request, 'accounts/auth/login.html')

from django.contrib.auth.views import PasswordResetView, PasswordResetCompleteView, PasswordResetConfirmView


class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/auth/password_reset.html"
    email_template_name = "accounts/auth/password_reset_email.html"
    subject_template_name = "accounts/auth/password_reset_subject.txt"
    success_url = None  # we override below

    def form_valid(self, form):
        # Run the parent logic (this sends the email)
        super().form_valid(form)
        # Render the same page, but pass a flag to show modal
        return self.render_to_response(
            self.get_context_data(show_modal=True)
        )

    def get_success_url(self):
        # Instead of redirecting to reset_password_done,
        # reload the same page with modal
        return self.request.path


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    def dispatch(self, request, *args, **kwargs):
        sweetify.success(
            request,
            'Success!',
            text='Your password has been reset successfully. Please log in.',
            button='OK',
            timer=10000,
            timerProgressBar=True
        )
        return redirect(reverse_lazy("accounts:login"))


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/auth/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


def clients_group(sender, instance, created, **kwargs):
    if created:
        try:
            group = Group.objects.get(name='clients')
            instance.user.groups.add(group)

        except Group.DoesNotExist as err:
            group = Group.objects.create(name='clients')
            instance.user.groups.add(group)


post_save.connect(clients_group, sender=Client)

def logout_view(request):
    logout(request)
    return redirect('accounts:login')




@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def account_profile(request):
    profile_pic = request.FILES.get('profile_pic')
    if request.method == "POST":
        fs = FileSystemStorage()
        filename = fs.save(profile_pic.name, profile_pic)
        fs.url(f'client/profile_pic/{filename}')
        client = Client.objects.filter(user=request.user)
        client.update(profile_pic=profile_pic)
    context = {
        'navbar': "profile",
    }
    return render(request, 'accounts/settings/profile.html', context)


@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def change_password(request):
    old_password = request.user.client.account_password
    old_pswd = request.POST.get('old_pswd')
    new_pswd1 = request.POST.get('new_pswd1')

    if request.method == "POST":
        if old_pswd == old_password:
            client_user = Client.objects.get(user=request.user)
            user = User.objects.get(email=request.user.email)
            user.set_password(new_pswd1)
            user.save()
            client_user.account_password = new_pswd1
            client_user.save(update_fields=['account_password'])
            user = authenticate(request, email=client_user.user.email, password=new_pswd1)
            login(request, user)
            sweetify.success(
            request,
            'Success!',
            text='Your password has been reset successfully.',
            button='OK',
            timer=10000,
            timerProgressBar=True
            )
            return redirect('accounts:change_password')

        elif old_pswd != old_password:

            sweetify.error(
            request,
            'Error!',
            text='Incorrect Password',
            button='OK',
            timer=10000,
            timerProgressBar=True
        )
            return redirect('accounts:change_password')
    context = {
        'navbar': "profile",
    }

    return render(request, 'accounts/settings/change_password.html', context)



@login_required(login_url="accounts:login")
@allowed_users(allowed_roles=['clients'])
@never_cache
def customer_support(request):
    if request.method == 'POST':
        user = request.user
        subject = request.POST.get('subject')
        message = request.POST.get('message') + str(' \n Sender is %s' % user)
        to_email = CompanyProfile.objects.first().forwarding_email
        email = EmailMultiAlternatives(
            subject, message, to=[to_email]
        )
        email.attach_alternative(message, 'text/html')
        email.send()

        return redirect('accounts:customer-support')
    context = {'navbar': "customer", }
    return render(request, 'accounts/customer_support.html', context)

@login_required(login_url='accounts:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def verification(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES)
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.user = request.user.client   # assign to Client
            kyc.save()

            # Send KYC email
            email_address = CompanyProfile.objects.first().forwarding_email
            EmailSender.kyc_email_sender(user=request.user, email=email_address)

            # Update client verification status
            client = request.user.client
            client.Verification_status = "Under Review"
            client.save(update_fields=['Verification_status'])

            return redirect('transaction:dashboard')
        else:
            # form invalid -> show errors
            return render(request, 'accounts/kyc.html', {'form': form})
    else:
        form = VerificationForm()

    return render(request, 'accounts/kyc.html', {'form': form})

