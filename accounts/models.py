from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
import random


def generate_customer_id():
    try:
        from .models import Customer  
        while True:
            cid = random.randint(1000, 9999)
            if not Customer.objects.filter(customer_id=cid).exists():
                return cid
    except:
        
        return random.randint(1000, 9999)




phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits"
)

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    serial_no = models.PositiveIntegerField(unique=True, null=True, blank=True)
    customer_id = models.PositiveIntegerField(unique=True, default=generate_customer_id)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, blank=True, null=True, validators=[phone_validator])
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def total_amount(self):
        return sum(t.selling_price for t in self.transactions.all())

    @property
    def total_paid(self):
        credits = sum(c.amount for c in self.credits.all())
        advance = sum(t.advance_amount for t in self.transactions.all())
        return credits + advance

    @property
    def balance(self):
        return self.total_amount - self.total_paid

    @property
    def is_due_1_month(self):
        one_month_ago = timezone.now() - timedelta(days=30)
        last_credit = self.credits.filter(date__isnull=False).order_by('-date').first()
        last_transaction = self.transactions.filter(date__isnull=False).order_by('-date').first()
        if not last_credit and not last_transaction:
            return True
        if last_credit:
            return last_credit.date < one_month_ago
        if last_transaction and last_transaction.date < one_month_ago:
            return True
        return False





PAYMENT_CHOICES = [
    ('CASH', 'CASH'),
    ('GPAY', 'GPAY'),
    ('PHONE PE', 'PHONE PE'),
]

class Transaction(models.Model):
    customer = models.ForeignKey(Customer, related_name='transactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    product = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100, null=True)
    quantity = models.PositiveIntegerField(default=1)

    
    original_price = models.PositiveIntegerField(default=0)   
    customer_price = models.PositiveIntegerField(default=0)   

    date = models.DateTimeField(null=True, blank=True)
    selling_price = models.PositiveIntegerField(default=0)  
    advance_amount = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=250, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True, choices=PAYMENT_CHOICES)
    original_cost = models.FloatField(default=0)

    def __str__(self):
        return f"{self.customer.name} - {self.product_name or self.product}"

    @property
    def profit(self):
        
        return (self.customer_price - self.original_price) * (self.quantity or 1)



class Credit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="credits")
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.customer.name} - Credit {self.amount}"


    
class MonthlyTurnover(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    month = models.IntegerField()
    year = models.IntegerField()
    sold = models.FloatField(default=0)
    paid = models.FloatField(default=0)
    balance = models.FloatField(default=0)
    profit = models.FloatField(default=0)   
    original_cost = models.FloatField(default=0)

    class Meta:
        unique_together = ('user', 'month', 'year')



class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(default=0)  
    customer_price = models.PositiveIntegerField(default=0)  
    stock = models.PositiveIntegerField(default=0)
    updated_at = models.DateField(null=True, blank=True)
    invested_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        
        stock = int(self.stock or 0)
        price = int(self.price or 0)

        self.invested_amount = stock * price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


    

class ProductStockHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="history")
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} updated on {self.updated_at}"

class UserSecurity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    security_question = models.CharField(max_length=255)
    security_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username





       

