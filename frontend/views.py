from django.shortcuts import render

from accounts.models import Investment, InvestmentCategory


# Create your views here.


def HomeView(request):
    categories = InvestmentCategory.objects.all()
    investments = Investment.objects.filter(is_active=True).select_related("category").prefetch_related("benefits")

    context = {
        "categories": categories,
        "investments": investments,
        'navbar':'home'
    }
    return render(request, 'frontend/home.html', context)

def AboutView(request):
    context = {
        'navbar':'about'
    }
    return render(request, 'frontend/about.html', context)


def PlanView(request):
    categories = InvestmentCategory.objects.all()
    investments = Investment.objects.filter(is_active=True).select_related("category").prefetch_related("benefits")

    context = {
        "categories": categories,
        "investments": investments,
        'navbar':'plans'
    }
    return render(request, 'frontend/plans.html', context)


def FaqView(request):
    context = {
        'navbar':'faq'
    }
    return render(request, 'frontend/faq.html', context)

def ContactView(request):
    context = {
        'navbar':'contact'
    }
    return render(request, 'frontend/contact.html', context)