
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from frontend.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap
}


urlpatterns = [
    path('dantech/', admin.site.urls),
    path("account/", include(("accounts.urls", "accounts"), namespace="accounts")),
    # include staff-only urls under a prefix
    path("boss/", include("accounts.boss_urls",)),

    path("transaction/", include(("transaction.urls", "transaction"), namespace="transaction")),
    path('', include('frontend.urls', namespace='frontend') ),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemaps'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.index_title = "Tradewest Admin"
admin.site.site_header = "Tradewest"


# handler404 = 'frontend.views.error_404_view'
# handler500 = 'frontend.views.error_500_view'
# handler403 = 'frontend.views.error_403_view'