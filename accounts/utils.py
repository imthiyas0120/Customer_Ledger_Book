from datetime import datetime
from django.db.models import Sum
from .models import Transaction, MonthlyTurnover
import requests

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

def send_sms(phone, message):
    print("SMS TO:", phone)
    print("MESSAGE:", message)

FAST2SMS_API_KEY = "cO34SIAmPDhoZe190TVluMbQqHUd5Ep7tGrWXyC2avNwRgsKxYGMlthue79s1Rcdn8EbWOkPSpT5QawD"

def send_sms(phone, message):
    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "route": "otp",
        "numbers": phone,
        "message": message,
    }

    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    # 🔥 THIS IS IMPORTANT
    print("FAST2SMS STATUS CODE:", response.status_code)
    print("FAST2SMS RESPONSE:", response.text)

    return response.json()