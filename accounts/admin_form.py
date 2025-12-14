from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import Client


class FixedCountryField(forms.ChoiceField):
    """
    A patched field that forces CountryField choices into a list,
    avoiding BlankChoiceIterator errors in admin templates.
    """
    def __init__(self, *args, **kwargs):
        blank_label = kwargs.pop("blank_label", "Select Country")
        required = kwargs.get("required", True)

        # get countries as list
        countries = list(CountryField().choices)

        # prepend blank option if required
        if required:
            countries = [('', blank_label)] + countries

        # plain select widget with Bootstrap
        widget = kwargs.pop(
            "widget",
            forms.Select(attrs={"class": "form-control"})
        )

        super().__init__(choices=countries, widget=widget, *args, **kwargs)
class ClientForm(forms.ModelForm):
    country = FixedCountryField(required=False)  # 👈 patched here

    class Meta:
        model = Client
        fields = "__all__"
