# context_processors.py
from accounts.models import CompanyProfile


def company_context(request):
    company = CompanyProfile.objects.first()
    if not company:
        # Provide safe defaults if no CompanyProfile exists
        class DefaultCompany:
            name = "My Company"
            domain = "https://example.com"
            logo = None
            favicon = None
            support_email = "support@example.com"
            forwarding_email = "forward@example.com"
            address = "123 Default Street"
            phone = "+0000000000"

        company = DefaultCompany()

    return {"company": company}
