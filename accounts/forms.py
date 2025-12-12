from django import forms
from .models import Customer, Transaction, Credit, Product

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
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address']


class TransactionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)   
        super().__init__(*args, **kwargs)

       
        if user:
            self.fields["product"].queryset = Product.objects.filter(user=user)
        else:
            self.fields["product"].queryset = Product.objects.none()

       
        self.fields['selling_price'].widget.attrs.pop('readonly', None)

    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),   
        required=True,
        label="Select Product"
    )

    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )

    quantity = forms.IntegerField(min_value=1, initial=1)

    class Meta:
        model = Transaction
        fields = [
            'product',
            'quantity',
            'selling_price',
            'advance_amount',
            'date',
            'payment_method',
        ]




class CreditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        if 'date' in self.fields:
            self.fields['date'].input_formats = ['%Y-%m-%dT%H:%M']

    class Meta:
        model = Credit
        fields = ['payment_method', 'amount', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'payment_method': forms.Select()
        }


class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address']
