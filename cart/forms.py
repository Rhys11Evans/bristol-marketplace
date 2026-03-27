from django import forms
from .models import Cart


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    cart_id = forms.IntegerField(widget=forms.HiddenInput)


class CreateCartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Weekly Shop"}),
        }


class UpdateQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)
