import os

from .settings import *

DEBUG = False
ALLOWED_HOSTS = ["16.16.183.63", "tradewests.com", "www.tradewests.com"]


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.zoho.com'
DEFAULT_FROM_EMAIL = 'CryptoTrade Globe<info@tradewests.com>'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'info@tradewests.com'
EMAIL_HOST_PASSWORD = 'Ctg@admin1212'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


CORS_ALLOWED_ORIGINS = [
    "https://tradewests.com",
    "https://www.tradewests.com",
    "http://16.171.140.202",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewests.com",
    "https://www.tradewests.com",
    "http://16.171.140.202",
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
