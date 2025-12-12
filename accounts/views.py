from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from .models import Customer, Transaction, Credit
from .forms import CustomerForm, TransactionForm, CreditForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
import os
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from datetime import datetime
from .models import MonthlyTurnover
from datetime import datetime
from .models import Product
from django.utils import timezone
from .models import ProductStockHistory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from .models import UserSecurity
from django.views.decorators.cache import never_cache


def test_email(request):
    send_mail(
        "Test from server",
        "Mail working successfully!",
        "imthiyasdjango@gmail.com",
        ["imthiyasdjango@gmail.com"],  
        fail_silently=False
    )
    return HttpResponse("Email sent from server!")


@never_cache
def customer_delete(request, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        
        return redirect('accounts:customer_list')

    if request.method == "POST":
        customer.delete()
        return redirect('accounts:customer_list')

    return render(request, "accounts/customer_delete_confirm.html", {
        "customer_id": customer_id
    })


def get_product_price(request, product_id):
    try:
        p = Product.objects.get(pk=product_id)
        return JsonResponse({
            "price": p.price,
            "customer_price": p.customer_price
        })
    except Product.DoesNotExist:
        return JsonResponse({"price": 0, "customer_price": 0})

def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("accounts:home")
        else:
            error = "Invalid username or password"

    return render(request, "accounts/login.html", {"error": error})

@csrf_protect
def signup(request):
    error_message = ""

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        question = request.POST.get("security_question")
        answer = request.POST.get("security_answer")

        if password1 != password2:
            error_message = "Passwords do not match!"
        elif User.objects.filter(username=username).exists():
            error_message = "This username already exists!"
        else:
            user = User.objects.create_user(
                username=username,
                password=password1,
                first_name=first_name
            )

            
            UserSecurity.objects.create(
                user=user,
                security_question=question,
                security_answer=answer.lower().strip()
            )

            login(request, user)
            return redirect("accounts:home")

    return render(request, "accounts/signup.html", {"error_message": error_message})


def forgot_password(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")

        if not username:
            error = "Please enter a username."
            return render(request, "accounts/forgot_password.html", {"error": error})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            error = "Username does not exist!"
            return render(request, "accounts/forgot_password.html", {"error": error})

        try:
            sec = UserSecurity.objects.get(user=user)
        except UserSecurity.DoesNotExist:
            error = "Security question not set for this user!"
            return render(request, "accounts/forgot_password.html", {"error": error})

        
        request.session["reset_user"] = username
        return redirect("accounts:reset_password")

    return render(request, "accounts/forgot_password.html")




def reset_password(request):
    username = request.session.get("reset_user")

    if not username:
        return redirect("accounts:forgot_password")

    user = User.objects.get(username=username)
    sec = UserSecurity.objects.get(user=user)

    if request.method == "POST":
        answer = request.POST.get("answer").lower().strip()

        if answer != sec.security_answer:
            return render(request, "accounts/security_question.html", {
                "username": username,
                "question": sec.security_question,
                "error": "Wrong answer!"
            })

        return redirect("accounts:save_new_password")

    return render(request, "accounts/security_question.html", {
        "username": username,
        "question": sec.security_question
    })




def save_new_password(request):
    username = request.session.get("reset_user")

    if not username:
        return redirect("accounts:forgot_password")

    user = User.objects.get(username=username)

    if request.method == "POST":
        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        if p1 != p2:
            return render(request, "accounts/set_new_password.html", {
                "username": username,
                "error": "Passwords do not match"
            })

        user.set_password(p1)
        user.save()
        request.session.flush()
        return redirect("login")

    return render(request, "accounts/set_new_password.html", {"username": username})


@login_required(login_url='login')
def home(request):
    customers = Customer.objects.all()[:10]
    
    username = request.user.first_name or request.user.username
    
    return render(request, 'accounts/home.html', {
        'customers': customers,
        'username': username,
    })






def calculator_view(request):
    return render(request, "accounts/calculator.html")


def customer_list(request):
    customers = Customer.objects.filter(user=request.user).order_by('serial_no')

    customer_data = []

    grand_total_amount = 0
    grand_total_paid = 0
    grand_total_balance = 0

    for cust in customers:
         
        transactions = cust.transactions.filter(user=request.user)

        
        credits = cust.credits.filter(user=request.user)
        total_selling = cust.transactions.aggregate(Sum('selling_price'))['selling_price__sum'] or 0
        total_advance = cust.transactions.aggregate(Sum('advance_amount'))['advance_amount__sum'] or 0
        total_credit = cust.credits.aggregate(Sum('amount'))['amount__sum'] or 0

        total_paid = total_advance + total_credit
        balance = total_selling - total_paid

        
        grand_total_amount += total_selling
        grand_total_paid += total_paid
        grand_total_balance += balance

        customer_data.append({
            'id': cust.id,
            'serial_no': cust.serial_no,
            'customer_id': cust.customer_id,
            'name': cust.name,
            'phone': cust.phone,
            'total_selling': total_selling,
            'total_paid': total_paid,
            'balance': balance,
            'is_due_1_month': cust.is_due_1_month,
        })

    return render(request, "accounts/customer_list.html", {
        "customers": customer_data,
        "grand_total_amount": grand_total_amount,
        "grand_total_paid": grand_total_paid,
        "total_balance_all": grand_total_balance,
    })

from django.db.models import Sum
from django.db.models import Q

def product_list(request):
    query = request.GET.get("q", "").strip()

    products = Product.objects.filter(user=request.user).order_by("id")

    if query:
        if query.isdigit():
            products = products.filter(
                Q(id=query) | Q(stock=query)
            )
        else:
            products = products.filter(name__icontains=query)

    
    total_invested = products.aggregate(
        total=Sum('invested_amount')
    )['total'] or 0

    return render(request, 'accounts/product_list.html', {
        'products': products,
        'query': query,
        'total_invested': total_invested,   
    })




def product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    history = product.history.order_by('-updated_at')

    return render(request, 'accounts/product_view.html', {
        'product': product,
        'history': history
    })

def save_stock_history(product, old_stock, new_stock, user):
    if old_stock != new_stock:
        ProductStockHistory.objects.create(
            product=product,
            stock_before=old_stock,
            stock_after=new_stock,
            user=user
        )




from django.utils import timezone
from .models import ProductStockHistory

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":

        old_stock = product.stock

        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.customer_price = request.POST.get("customer_price")   

        new_stock = int(request.POST.get("stock"))
        product.stock = new_stock

        product.updated_at = request.POST.get("updated_at")

        product.save()

        if old_stock != new_stock:
            ProductStockHistory.objects.create(
                product=product,
                stock_before=old_stock,
                stock_after=new_stock
            )

        return redirect("accounts:product_list")

    return render(request, "accounts/edit_product.html", {"product": product})



def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect("accounts:product_list")


def customer_add(request):
    customer_form = CustomerForm()
    transaction_form = TransactionForm(user=request.user)
    products = Product.objects.filter(user=request.user)

    if request.method == "POST":
        customer_form = CustomerForm(request.POST)
        transaction_form = TransactionForm(request.POST, user=request.user)

        if customer_form.is_valid() and transaction_form.is_valid():

            
            customer = customer_form.save(commit=False)
            customer.user = request.user

            last_customer = Customer.objects.filter(
                user=request.user
            ).exclude(serial_no__isnull=True).order_by('-serial_no').first()

            if last_customer and last_customer.serial_no:
                customer.serial_no = last_customer.serial_no + 1
            else:
                customer.serial_no = 1

            customer.save()

           
            transaction = transaction_form.save(commit=False)
            transaction.customer = customer
            transaction.user = request.user

            selected_product = transaction_form.cleaned_data['product']
            quantity = transaction_form.cleaned_data['quantity']

            transaction.product = selected_product
            transaction.product_name = selected_product.name

            transaction.original_cost = selected_product.price
            transaction.customer_price = selected_product.customer_price
            transaction.selling_price = selected_product.customer_price * quantity

            
            if selected_product.stock >= quantity:
                selected_product.stock -= quantity
                selected_product.updated_at = timezone.now()
                selected_product.save()
            else:
                transaction_form.add_error("quantity", "Not enough stock!")
                return render(request, "accounts/customer_form.html", {
                    "customer_form": customer_form,
                    "transaction_form": transaction_form,
                    "products": products
                })

            transaction.save()
            return redirect("accounts:customer_list")

    return render(request, "accounts/customer_form.html", {
        "customer_form": customer_form,
        "transaction_form": transaction_form,
        "products": products
    })





def customer_accounts(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    transactions = customer.transactions.order_by('-date')

   
    if request.method == "POST":
        credit_form = CreditForm(request.POST, customer=customer)
        if credit_form.is_valid():
            credit = credit_form.save(commit=False)
            credit.customer = customer
            credit.save()
            return redirect("accounts:customer_ledger", customer.id)
    else:
        credit_form = CreditForm(customer=customer)

    
    for t in transactions:
        t.balance = t.selling_price - t.advance_amount

    
    total_selling = transactions.aggregate(total=Sum('selling_price'))['total'] or 0
    total_advance = transactions.aggregate(total=Sum('advance_amount'))['total'] or 0

   
    credits_ordered = customer.credits.order_by('date')  

    running_balance = total_selling - total_advance

    for c in credits_ordered:
        running_balance -= c.amount
        c.balance = running_balance  

    
    credits_list = list(credits_ordered)

    
    credits_list.sort(key=lambda x: x.balance, reverse=True)


    
    total_credit = sum(c.amount for c in credits_ordered)
    final_balance = running_balance

    context = {
        'customer': customer,
        'transactions': transactions,
        'credits': credits_list,     
        'total_selling': total_selling,
        'total_advance': total_advance,
        'total_credit': total_credit,
        'balance': final_balance,
        'credit_form': credit_form,
    }


    return render(request, 'accounts/customer_ledger.html', context)



from .models import Product

def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        customer_price = request.POST.get("customer_price")
        stock = request.POST.get("stock")
        updated_at = request.POST.get("updated_at")

        Product.objects.create(
            name=name,
            price=price,
            customer_price=customer_price,
            stock=stock,
            updated_at=updated_at,
            user=request.user   
        )

        return redirect("accounts:product_list")

    return render(request, "accounts/add_product.html")




from .models import ProductStockHistory
from django.utils import timezone

def add_transaction(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    products = Product.objects.filter(user=request.user)
    if request.method == "POST":
        form = TransactionForm(request.POST,user=request.user)
        if form.is_valid():
            t = form.save(commit=False)
            t.customer = customer
            t.user = request.user
            t.product = form.cleaned_data['product']
            t.product_name = t.product.name
            t.original_price = t.product.price
            t.customer_price = t.product.customer_price
            t.selling_price = t.customer_price * t.quantity

           
            if t.product.stock >= t.quantity:
                old_stock = t.product.stock
                t.product.stock -= t.quantity
                t.product.updated_at = timezone.now()
                t.product.save()
                
            else:
                form.add_error("quantity", "Not enough stock!")
                return render(request, "accounts/transaction_form.html", {"form": form, "products": products, "customer": customer})

            t.save()
            return redirect("accounts:customer_ledger", customer_id=customer.id)
    else:
        form = TransactionForm(user=request.user)
    return render(request, "accounts/transaction_form.html", {"form": form, "products": products, "customer": customer})









def add_credit(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == "POST":
        form = CreditForm(request.POST)
        if form.is_valid():
            credit = form.save(commit=False)
            credit.customer = customer
            credit.user = request.user
            credit.save()
            return redirect("customer_credit", customer_id=customer.id)
    else:
        form = CreditForm()

    credits = customer.credits.order_by('-date')

    
    total_credit = credits.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, "customer_credit.html", {
        "form": form,
        "credits": credits,
        "total_credit": total_credit,
    })





def search_customers(request):
    query = request.GET.get("q", "").strip()

    base_queryset = Customer.objects.filter(user=request.user)

    customers = base_queryset.none()

    if query:
        if query.isdigit():
            if len(query) > 4:
               
                customers = base_queryset.filter(phone__icontains=query)
            else:
                
                customers = base_queryset.filter(
                    Q(customer_id__icontains=query) |
                    Q(phone__icontains=query) |
                    Q(name__icontains=query)
                )
        else:
            
            customers = base_queryset.filter(name__icontains=query)

    else:
        customers = base_queryset.order_by("serial_no")

    
    customer_data = []
    grand_total_amount = 0
    grand_total_paid = 0
    grand_total_balance = 0

    for cust in customers:
        total_selling = cust.transactions.aggregate(Sum('selling_price'))['selling_price__sum'] or 0
        total_advance = cust.transactions.aggregate(Sum('advance_amount'))['advance_amount__sum'] or 0
        total_credit = cust.credits.aggregate(Sum('amount'))['amount__sum'] or 0

        total_paid = total_advance + total_credit
        balance = total_selling - total_paid

        grand_total_amount += total_selling
        grand_total_paid += total_paid
        grand_total_balance += balance

        customer_data.append({
            'id': cust.id,
            'customer_id': cust.customer_id,
            'serial_no': cust.serial_no,
            'name': cust.name,
            'phone': cust.phone,
            'total_selling': total_selling,
            'total_paid': total_paid,
            'balance': balance,
            'is_due_1_month': cust.is_due_1_month,
        })

    return render(request, "accounts/customer_list.html", {
        "customers": customer_data,
        "grand_total_amount": grand_total_amount,
        "grand_total_paid": grand_total_paid,
        "total_balance_all": grand_total_balance,
    })








def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("accounts:customer_list")
    else:
        form = CustomerForm(instance=customer)

    return render(request, "accounts/customer_edit.html", {
        "form": form,
        "customer": customer,
        "edit_mode": True
    })


def credit_edit(request, credit_id):
    credit = get_object_or_404(Credit, id=credit_id)
    customer = credit.customer

    if request.method == "POST":
        form = CreditForm(request.POST, instance=credit)
        if form.is_valid():
            form.save()
            return redirect("accounts:customer_ledger", customer.id)
    else:
        form = CreditForm(instance=credit)

    return render(request, "accounts/credit_form.html", {
        "form": form,
        "customer": customer,
        "edit_mode": True
    })

def credit_delete(request, credit_id):
    credit = get_object_or_404(Credit, id=credit_id)
    customer_id = credit.customer.id

    if request.method == "POST":
        credit.delete()
        return redirect("accounts:customer_ledger", customer_id)

    return render(request, "accounts/credit_delete_confirm.html", {
        "credit": credit
    })



def transaction_edit(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    customer = transaction.customer
    old_quantity = transaction.quantity
    old_product = transaction.product

    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            updated_transaction = form.save(commit=False)
            new_product = form.cleaned_data["product"]
            new_quantity = form.cleaned_data["quantity"]

            
            if old_product == new_product:

                if new_quantity != old_quantity:
                    product = new_product

                    before = product.stock
                    after = before + old_quantity - new_quantity  

                    product.stock = after
                    product.save()

                    ProductStockHistory.objects.create(
                        product=product,
                        stock_before=before,
                        stock_after=after
                    )

            else:
                
                old_before = old_product.stock
                old_after = old_before + old_quantity
                old_product.stock = old_after
                old_product.save()

                ProductStockHistory.objects.create(
                    product=old_product,
                    stock_before=old_before,
                    stock_after=old_after
                )

                
                new_before = new_product.stock
                new_after = new_before - new_quantity
                new_product.stock = new_after
                new_product.save()

                ProductStockHistory.objects.create(
                    product=new_product,
                    stock_before=new_before,
                    stock_after=new_after
                )

            updated_transaction.save()

            return redirect("accounts:customer_ledger", customer.id)

    else:
        form = TransactionForm(instance=transaction)

    return render(request, "accounts/transaction_form.html", {
        "form": form,
        "customer": customer,
        "edit_mode": True
    })



def transaction_delete(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    product = transaction.product
    qty = transaction.quantity
    customer_id = transaction.customer.id

    if request.method == "POST":
        if product:
            before = product.stock
            after = before + qty     

            product.stock = after
            product.save()

            
            ProductStockHistory.objects.create(
                product=product,
                stock_before=before,
                stock_after=after
            )

        transaction.delete()
        return redirect("accounts:customer_ledger", customer_id)

    return render(request, "accounts/transaction_delete_confirm.html", {
        "transaction": transaction
    })



def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == "POST":

        
        for t in customer.transactions.all():
            if t.product:
                before = t.product.stock
                after = before + t.quantity

                t.product.stock = after
                t.product.save()

                ProductStockHistory.objects.create(
                    product=t.product,
                    stock_before=before,
                    stock_after=after
                )

        customer.delete()
        return redirect("accounts:customer_list")   

    return render(request, 'accounts/customer_delete_confirm.html', {
        "customer": customer,
        "customer_id": customer_id
    })



def turnover_page(request):
    
    save_monthly_turnover(request.user)

    
    customers = Customer.objects.filter(user=request.user)

    
    total_sold = Transaction.objects.filter(customer__in=customers).aggregate(
        total=Sum('selling_price'))['total'] or 0

    
    total_advance = Transaction.objects.filter(customer__in=customers).aggregate(
        total=Sum('advance_amount'))['total'] or 0

    
    total_credit_payments = Credit.objects.filter(customer__in=customers).aggregate(
        total=Sum('amount'))['total'] or 0

    
    total_paid = total_advance + total_credit_payments

    total_balance = total_sold - total_paid

    
    today = datetime.today()
    month = today.month
    year = today.year

    try:
        record = MonthlyTurnover.objects.get(month=month, year=year, user=request.user)
        monthly_sold = record.sold
        monthly_paid = record.paid
        monthly_balance = record.balance
        monthly_profit = record.profit
        monthly_original_cost = record.original_cost
    except MonthlyTurnover.DoesNotExist:
        monthly_sold = monthly_paid = monthly_balance = monthly_profit = monthly_original_cost = 0

    
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    records = MonthlyTurnover.objects.filter(year=year, user=request.user)
    rec_dict = {r.month: r for r in records}

    monthly_data = []
    for m in range(1, 13):
        if m in rec_dict:
            r = rec_dict[m]
            monthly_data.append({
                "month": months[m - 1],
                "sold": r.sold,
                "original_cost": r.original_cost,
                "profit": r.profit,
                "paid": r.paid,
                "balance": r.balance,
            })
        else:
            monthly_data.append({
                "month": months[m - 1],
                "sold": 0,
                "original_cost": 0,
                "profit": 0,
                "paid": 0,
                "balance": 0,
            })

    return render(request, "accounts/turnover.html", {
        "total_sold": total_sold,
        "total_paid": total_paid,
        "total_balance": total_balance,
        "monthly_sold": monthly_sold,
        "monthly_paid": monthly_paid,
        "monthly_balance": monthly_balance,
        "monthly_profit": monthly_profit,
        "monthly_original_cost": monthly_original_cost,
        "monthly_data": monthly_data,
    })




def save_monthly_turnover(user):
    """
    Rebuild MonthlyTurnover rows for the given user for the current year.
    Important: use customer->transactions and customer->credits so we don't
    miss credits that have no `user` field, or where credit.user wasn't set.
    """
    now = datetime.now()
    year = now.year

    
    MonthlyTurnover.objects.filter(user=user, year=year).delete()

    
    customers = Customer.objects.filter(user=user)

    for month in range(1, 13):
        
        trans = Transaction.objects.filter(
            customer__in=customers,
            date__month=month,
            date__year=year
        )

        
        credits = Credit.objects.filter(
            customer__in=customers,
            date__month=month,
            date__year=year
        )

        
        if not trans.exists() and not credits.exists():
            MonthlyTurnover.objects.create(
                user=user,
                month=month,
                year=year,
                sold=0,
                paid=0,
                balance=0,
                profit=0,
                original_cost=0
            )
            continue

        
        sold = trans.aggregate(total=Sum('selling_price'))['total'] or 0

        
        advance_paid = trans.aggregate(total=Sum('advance_amount'))['total'] or 0

        
        credit_paid = credits.aggregate(total=Sum('amount'))['total'] or 0

        paid = advance_paid + credit_paid

        original_cost = 0
        profit = 0
        for t in trans:
            
            unit_cost = None
            if getattr(t, 'original_price', None):
                unit_cost = t.original_price
            elif t.product:
                unit_cost = t.product.price
            else:
                unit_cost = 0

            cost_for_line = (unit_cost or 0) * (t.quantity or 1)
            original_cost += cost_for_line
            profit += (t.selling_price or 0) - cost_for_line

        
        MonthlyTurnover.objects.create(
            user=user,
            month=month,
            year=year,
            sold=sold,
            paid=paid,
            balance=sold - paid,
            profit=profit,
            original_cost=original_cost
        )






def export_customer_pdf(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    transactions = customer.transactions.all()
    credits = customer.credits.all()

    response = HttpResponse(content_type='application/pdf')
    filename = f"{customer.name}_ledger.pdf"
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans-Bold.ttf")))


    
    pdf.setStrokeColorRGB(0, 0, 0)
    pdf.setLineWidth(2)
    pdf.rect(20, 20, width - 40, height - 40)

   

    y = height - 60

    
    logo_path = os.path.join(settings.BASE_DIR, "static", "accounts", "logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 40, y - 70, width=90, height=90)

    
    pdf.setFont("DejaVuSans-Bold", 24)
    pdf.drawString(150, y, "Nizamuddin Enterprises")
    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(150, y - 20, "Phone: +91 9701640585")
    pdf.drawString(150, y - 40, "Address: Borabanda, Hyderabad, Telangana")
    y -= 120

    
    pdf.setFont("DejaVuSans", 16)
    pdf.drawString(40, y, "Customer Details")
    y -= 25
    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(40, y, f"Name     : {customer.name}")
    y -= 18
    pdf.drawString(40, y, f"Phone    : {customer.phone}")
    y -= 18
    pdf.drawString(40, y, f"Address  : {customer.address}")
    y -= 35

    
    pdf.setFont("DejaVuSans", 16)
    pdf.drawString(40, y, "Transactions")
    y -= 20

    t_data = [["Date", "Product", "Sell.Price", "Advance", "Balance", "Payment Method"]]

    for t in transactions:
        balance_row = t.selling_price - t.advance_amount
        t_data.append([
            t.date.strftime("%d-%m-%Y") if t.date else "—",
            t.product_name,
            f"₹{t.selling_price}",
            f"₹{t.advance_amount}",
            f"₹{balance_row}",
            t.payment_method or ""
        ])

    t_table = Table(t_data, colWidths=[70, 130, 70, 70, 70, 100])
    t_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    t_table.wrapOn(pdf, 40, y)
    t_table.drawOn(pdf, 40, y - len(t_data) * 18)
    y -= len(t_data) * 18 + 40

    
    pdf.setFont("DejaVuSans", 16)
    pdf.drawString(40, y, "Payments Received")
    y -= 20

    c_data = [["Date", "Amount", "Payment Method"]]

    for c in credits:
        date_str = c.date.strftime("%d-%m-%Y") if c.date else "_"
        c_data.append([
            date_str,
            f"₹{c.amount}",
            c.payment_method or ""
        ])

    c_table = Table(c_data, colWidths=[100, 80, 190])
    c_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgreen),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    c_table.wrapOn(pdf, 40, y)
    c_table.drawOn(pdf, 40, y - len(c_data) * 18)
    y -= len(c_data) * 18 + 40

    
    pdf.setFont("DejaVuSans", 16)
    pdf.drawString(40, y, "Summary")
    y -= 25

    total_selling = sum(t.selling_price for t in transactions)
    total_advance = sum(t.advance_amount for t in transactions)
    total_paid = sum(c.amount for c in credits)
    balance = total_selling - total_advance - total_paid

    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(40, y, f"Total Selling        : ₹{total_selling}")
    y -= 18
    pdf.drawString(40, y, f"Total Paid           : ₹{total_paid}")
    y -= 18
    pdf.drawString(40, y, f"Balance Remaining    : ₹{balance}")

    
    stamp_path = os.path.join(settings.BASE_DIR, "static", "accounts", "stamp.jpg")

    if os.path.exists(stamp_path):

        stamp_size = 130

        
        x_pos = width - stamp_size - 30     
        y_pos = 45                          

        
        x_pos -= 15     
        y_pos += 20     

        pdf.saveState()
        pdf.translate(x_pos + stamp_size/2, y_pos + stamp_size/2)
        pdf.rotate(30)

        pdf.drawImage(
            ImageReader(stamp_path),
            -stamp_size/2,
            -stamp_size/2,
            width=stamp_size,
            height=stamp_size,
            mask='auto'
        )
        pdf.restoreState()





    
    pdf.setFont("DejaVuSans", 10)
    pdf.setFillColor(colors.darkgray)

    footer_y = 40
    pdf.drawString(40, footer_y, "Nizamuddin Enterprises © 2025· Hyderabad · Telangana · India - 500018")
    pdf.drawString(40, footer_y - 12, "Phone: +91 9701640585 | Thank you for your business!")

    pdf.showPage()
    pdf.save()
    return response







    

