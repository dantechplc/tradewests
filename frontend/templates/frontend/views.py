# from django.shortcuts import render
#
# from accounts.decorators import unauthenticated_user
#
#
# # Create your views here.
# @unauthenticated_user
# def HomeView(request):
#     context = {
#         'navbar':'home'
#     }
#     return render(request, 'frontend/home.html', context)
#
# @unauthenticated_user
# def MarketView(request):
#     context = {
#         'navbar':'markets'
#     }
#     return render(request, 'frontend/market.html', context)
#
# @unauthenticated_user
# def AboutView(request):
#     context = {
#         'navbar':'about'
#     }
#     return render(request, 'frontend/about.html', context)
# @unauthenticated_user
# def ContactView(request):
#     context = {
#         'navbar':'contact'
#     }
#     return render(request, 'frontend/contact.html', context)
# @unauthenticated_user
# def CustomerView(request):
#     context = {
#         'navbar':'customer'
#     }
#     return render(request, 'frontend/customer.html', context)
# @unauthenticated_user
# def LegalView(request):
#     context = {
#         'navbar':'legal'
#     }
#     return render(request, 'frontend/legal.html', context)
#
#
#
# def error_404_view(request, exception):
#     return render(request, 'frontend/404.html')
#
#
# def error_500_view(request):
#     return render(request, 'frontend/500.html')
#
#
# def error_403_view(request, exception=None):
#     return render(request, 'frontend/403.html',status=403)
#
