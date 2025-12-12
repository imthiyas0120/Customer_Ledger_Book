from datetime import datetime
from django.db.models import Sum
from .models import Transaction, MonthlyTurnover

def save_monthly_turnover():
    now = datetime.now()
    month = now.month
    year = now.year

   
    monthly_transactions = Transaction.objects.filter(
        date__month=month,
        date__year=year
    )

    
    sold = monthly_transactions.aggregate(total=Sum('selling_price'))['total'] or 0
    paid = monthly_transactions.aggregate(total=Sum('advance_amount'))['total'] or 0
    balance = sold - paid

   
    turnover, created = MonthlyTurnover.objects.get_or_create(
        month=month,
        year=year
    )

    turnover.sold = sold
    turnover.paid = paid
    turnover.balance = balance
    turnover.save()
