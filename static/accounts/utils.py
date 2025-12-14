import string
import random

def generate_ref_code():
    chars = string.ascii_uppercase + string.digits  # A-Z + 0-9
    while True:
        code = ''.join(random.choices(chars, k=4))
        from .models import Client
        if not Client.objects.filter(referral_code=code).exists():
            return code
