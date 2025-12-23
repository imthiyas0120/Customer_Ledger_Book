from django import forms
from .models import Customer, Transaction, Credit, Product
from datetime import date
from django import forms
from .models import ProductBrand

class CustomerForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={
            'pattern': '[0-9]{10}',
            'title': 'Enter 10 digit mobile number',
            'maxlength': '10',
        })
    )

    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            
        })
    )



    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address','customer_mode']
        widgets = {
            'customer_mode': forms.Select(
                attrs={'required': True}
            )
        }


class TransactionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            
            self.fields["product"].queryset = Product.objects.filter(user=self.user)
            self.fields["brand"].queryset = ProductBrand.objects.filter(user=self.user)
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["brand"].queryset = ProductBrand.objects.none()

        
        self.product_stock_map = {
            p.id: p.stock for p in Product.objects.filter(user=self.user)
        }

    brand = forms.ModelChoiceField(
        queryset=ProductBrand.objects.none(),
        required=False,
        empty_label="---------"
    )

    quantity = forms.IntegerField(min_value=1)

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "max": date.today().isoformat()
            }
        ),
        required=True
    )

    class Meta:
        model = Transaction
        fields = [
            "product",
            "brand",
            "quantity",
            "selling_price",
            "advance_amount",
            "date",
            "payment_method",
        ]

    def clean_date(self):
        d = self.cleaned_data.get("date")
        if d and d > date.today():
            raise forms.ValidationError("Future date not allowed")
        return d


from django import forms
from .models import CompanyDetails

class CompanyDetailsForm(forms.ModelForm):
    class Meta:
        model = CompanyDetails
        fields = ["company_name", "address"]
        widgets = {
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Company Name"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control  small-textarea",
                "placeholder": "Company Address",
                "rows": 2,
            }),
        }


class CreditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Credit
        fields = ['payment_method', 'amount', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date','max': date.today().isoformat()}),
            'payment_method': forms.Select()
        }



class CustomerEditForm(forms.ModelForm):
    created_at = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date','max': date.today().isoformat()}),
        required=True,
        label="Date"
    )

    def clean_created_at(self):
        d = self.cleaned_data.get("created_at")
        if d and d > date.today():
            raise forms.ValidationError("Future date not allowed")
        return d
    
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address','created_at','customer_mode',]

        widgets = {
            'customer_mode': forms.Select()
        }
