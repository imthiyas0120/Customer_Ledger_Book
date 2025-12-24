from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, F
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
from .models import Product,ProductVariant
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
from django.http import JsonResponse
from .forms import CustomerEditForm
from .models import ProductYearlyTurnover
import random
from django.contrib import messages
from .models import PasswordResetOTP
from .utils import send_sms
from django.core.mail import send_mail
from .models import EmailOTP, Profile
from django.contrib.auth.decorators import login_required
from .models import CompanyDetails
from .forms import CompanyDetailsForm
from accounts.models import Customer, CompanyDetails


@login_required
def user_details(request):
    company = CompanyDetails.objects.filter(user=request.user).first()
    customer = Customer.objects.filter(user=request.user).first()

    return render(request, "accounts/user_details.html", {
        "user": request.user,
        "company": company,
         "customer": customer,
    })

@login_required
def company_details(request):
    company, created = CompanyDetails.objects.get_or_create(
        user=request.user,
        defaults={"company_name": "", "address": ""}
    )

    if request.method == "POST":
        form = CompanyDetailsForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect("accounts:user_details")
    else:
        form = CompanyDetailsForm(instance=company)

    return render(request, "accounts/company_details.html", {
        "form": form
    })

def test_email(request):
    send_mail(
        "Test from server",
        "Mail working successfully!",
        "imthiyasdjango@gmail.com",
        ["imthiyasdjango@gmail.com"],  
        fail_silently=False
    )
    return HttpResponse("Email sent from server!")

def save_yearly_product_turnover(user):
    year = datetime.now().year

  
    total_purchase_cost = Product.objects.filter(
        user=user
    ).aggregate(
        total=Sum("invested_amount")
    )["total"] or 0

    customers = Customer.objects.filter(user=user)

    
    total_sales = Transaction.objects.filter(
        customer__in=customers
    ).aggregate(
        total=Sum("selling_price")
    )["total"] or 0

    
    sold_original_cost = 0
    transactions = Transaction.objects.filter(customer__in=customers)

    for t in transactions:
        sold_original_cost += (t.original_price or 0) * (t.quantity or 1)

   
    total_profit = total_sales - sold_original_cost

    
    ProductYearlyTurnover.objects.update_or_create(
        user=user,
        year=year,
        defaults={
            "total_purchase_cost": total_purchase_cost,
            "total_sales": total_sales,
            "total_sales_original_cost": sold_original_cost, 
            "total_profit": total_profit,
        }
    )





def product_autocomplete(request):
    q = request.GET.get("q", "")
    print("AUTOCOMPLETE QUERY:", q)  

    products = (
        ProductVariant.objects
        .filter(user=request.user, name__icontains=q)
        .values_list("name", flat=True)
        .distinct()
    )

    print("RESULT:", list(products))  

    return JsonResponse(list(products), safe=False)



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


@login_required
def product_details(request):
    variants = ProductVariant.objects.filter(user=request.user)

    if request.method == "POST":
        name = request.POST.get("product_name", "").strip()
        if name:
            ProductVariant.objects.get_or_create(
                user=request.user,
                name=name
            )
        return redirect("accounts:product_details")

    return render(request, "accounts/product_details.html", {
        "variants": variants
    })



def edit_product_variant(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk, user=request.user)

    if request.method == "POST":
        name = request.POST.get("product_name", "").strip()

        if name:
            variant.name = name
            variant.save()

        return redirect("accounts:product_details")

    return render(request, "accounts/edit_product1.html", {
        "variant": variant,
        "today": date.today()
    })



def delete_product_variant(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)

    if request.method == "POST":
        variant.delete()

    return redirect("accounts:product_details")


def get_product_price(request, product_id):
    try:
        p = Product.objects.get(pk=product_id)
        return JsonResponse({
            "price": p.price,
            "customer_price": p.customer_price
        })
    except Product.DoesNotExist:
        return JsonResponse({"price": 0, "customer_price": 0})


@never_cache
def login_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:home")

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

from django.db import transaction
@csrf_protect
def signup(request):
    error_message = ""

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        
        if password1 != password2:
            error_message = "Passwords do not match"

        elif User.objects.filter(username=username).exists():
            error_message = "Username already exists"

        elif User.objects.filter(email=email).exists():
            error_message = "Email already registered"

        else:
            try:
                
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password1,
                        first_name=first_name,
                        is_active=True
                    )

                    Profile.objects.create(user=user, phone=phone)

               
                login(request, user)
                return redirect("accounts:home")

            except Exception:
                error_message = "Something went wrong. Please try again."

    return render(
        request,
        "accounts/signup.html",
        {"error_message": error_message}
    )
def forgot_username(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(
                request,
                "If this email is registered, you will receive your username."
            )
            return redirect("accounts:forgot_username")

        
        send_mail(
            subject="Your Username – Nizamuddin Enterprises",
            message=f"""
            Hello {user.first_name},

            You requested to recover your username.

            Your username is:
            ➡ {user.username}

            If you did not request this, please ignore this email.

            – Nizamuddin Enterprises
                        """,
            from_email=None, 
            recipient_list=[email],
        )

        messages.success(
            request,
            "If this email is registered, you will receive your username."
        )
        return redirect("login")

    return render(request, "accounts/forgot_username.html")

def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")

       
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect("accounts:forgot_password")

       
        email = user.email

        if not email:
            messages.error(request, "No email linked with this account")
            return redirect("accounts:forgot_password")

        
        EmailOTP.objects.filter(user=user).delete()

        
        otp = str(random.randint(100000, 999999))

        
        print("EMAIL OTP:", otp)
        print("EMAIL:", email)

        
        EmailOTP.objects.create(user=user, otp=otp)

       
        send_mail(
            subject="Password Reset OTP",
            message=f"""
        Hello {user.first_name},

        Your OTP to reset your password is: {otp}

        This OTP is valid for 5 minutes.
        Do not share this OTP with anyone.

        – Nizamuddin Enterprises
        """,
            from_email=None,          
            recipient_list=[email],
        )

        
        request.session["reset_user_id"] = user.id

        messages.success(request, "OTP sent to your registered email")
        return redirect("accounts:verify_otp")

    return render(request, "accounts/forgot_password.html")


    

def verify_otp(request):
    user_id = request.session.get("reset_user_id")

    if not user_id:
        messages.error(request, "Session expired. Try again.")
        return redirect("accounts:forgot_password")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect("accounts:forgot_password")

    if request.method == "POST":
        otp_entered = request.POST.get("otp", "").strip()

       
        otp_obj = EmailOTP.objects.filter(
            user=user,
            otp=otp_entered
        ).first()

        if not otp_obj:
            messages.error(request, "Invalid OTP")
            return redirect("accounts:verify_otp")

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired")
            return redirect("accounts:forgot_password")

        
        otp_obj.delete()
        messages.success(request, "OTP verified successfully")
        return redirect("accounts:reset_password")

    return render(request, "accounts/verify_otp.html")




def reset_password(request):
    user_id = request.session.get("reset_user_id")

    if not user_id:
        return redirect("accounts:forgot_password")

    if request.method == "POST":
        password = request.POST.get("password")

        user = User.objects.get(id=user_id)
        user.set_password(password)
        user.save()

        PasswordResetOTP.objects.filter(user=user).delete()
        request.session.flush()

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "accounts/reset_password.html")

def resend_otp(request):
    user_id = request.session.get("reset_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect("accounts:forgot_password")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect("accounts:forgot_password")

    email = user.email
    if not email:
        messages.error(request, "Email not available.")
        return redirect("accounts:forgot_password")

    
    EmailOTP.objects.filter(user=user).delete()

    
    otp = str(random.randint(100000, 999999))
    EmailOTP.objects.create(user=user, otp=otp)

   
    print("RESEND OTP:", otp)

   
    send_mail(
        subject="Resend OTP – Password Reset",
        message=f"""
        Hello {user.first_name},

        Your new OTP to reset your password is: {otp}

        This OTP is valid for 5 minutes.
        Do not share this OTP with anyone.

        – Nizamuddin Enterprises
        """,
        from_email=None,
        recipient_list=[email],
    )

    messages.success(request, "New OTP sent to your registered email")
    return redirect("accounts:verify_otp")



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


@never_cache
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
    customers = Customer.objects.filter(user=request.user).order_by('serial_no')   # ✅ DATE ASCENDING

    customer_data = []

    grand_total_amount = 0
    grand_total_paid = 0
    grand_total_balance = 0

    for cust in customers:

        total_selling = cust.transactions.aggregate(
            Sum('selling_price')
        )['selling_price__sum'] or 0

        total_advance = cust.transactions.aggregate(
            Sum('advance_amount')
        )['advance_amount__sum'] or 0

        total_credit = cust.credits.aggregate(
            Sum('amount')
        )['amount__sum'] or 0

        total_paid = total_advance + total_credit
        balance = total_selling - total_paid

        grand_total_amount += total_selling
        grand_total_paid += total_paid
        grand_total_balance += balance

       
        product_names = (
                cust.transactions
                .values_list("product_name", flat=True)
                .distinct()
                )

        product_names_str = ", ".join(
            name for name in product_names if name
        )
        customer_data.append({
            'id': cust.id,
            'serial_no': cust.serial_no,
            'customer_id': cust.customer_id,
            'created_at': cust.created_at,
            'name': cust.name,
            'phone': cust.phone,
            'products': product_names_str,  
            'total_selling': total_selling,
            'total_paid': total_paid,
            'balance': balance,
            'customer_mode': cust.customer_mode,
            'is_due': cust.is_due,
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
        product.price = int(request.POST.get("price"))
        product.customer_price = int(request.POST.get("customer_price"))

        new_stock = int(request.POST.get("stock"))

       
        if new_stock > old_stock:
            added_stock = new_stock - old_stock
            product.invested_amount += added_stock * product.price

       
        product.stock = new_stock
        product.updated_at = request.POST.get("updated_at")
        product.save()

        ProductStockHistory.objects.create(
            product=product,
            stock_before=old_stock,
            stock_after=new_stock,
            user=request.user
        )

        return redirect("accounts:product_list")

    return render(request, "accounts/edit_product.html", {"product": product, "today": date.today()})




def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect("accounts:product_list")

from datetime import date
import json
@login_required
def customer_add(request):

    products = Product.objects.filter(user=request.user)

    #  flag for instruction
    no_products = not products.exists()

    #  product_id → stock map
    product_stock = {
        str(p.id): p.stock for p in products
    }

    customer_form = CustomerForm()
    transaction_form = TransactionForm(user=request.user)

    if request.method == "POST":

        if no_products:
            messages.warning(
                request,
                "⚠️ First add at least one product before adding a customer."
            )
            return redirect("accounts:customer_add")

        customer_form = CustomerForm(request.POST)
        transaction_form = TransactionForm(request.POST, user=request.user)

        if customer_form.is_valid() and transaction_form.is_valid():

            customer = customer_form.save(commit=False)
            customer.user = request.user

            last_customer = Customer.objects.filter(
                user=request.user
            ).exclude(serial_no__isnull=True).order_by('-serial_no').first()

            customer.serial_no = last_customer.serial_no + 1 if last_customer else 1

            transaction_date = transaction_form.cleaned_data.get("date")
            if transaction_date:
                customer.created_at = transaction_date

            customer.save()

            transaction = transaction_form.save(commit=False)
            transaction.customer = customer
            transaction.user = request.user

            transaction_date = transaction_form.cleaned_data.get("date")

            if transaction_date:
                transaction.date = transaction_date
            else:
                transaction.date = customer.created_at or timezone.now()

            product = transaction_form.cleaned_data["product"]
            qty = transaction_form.cleaned_data["quantity"]

            transaction.product = product
            transaction.product_name = product.name
            transaction.original_price = product.price
            transaction.customer_price = product.customer_price
            transaction.selling_price = product.customer_price * qty
            original_total = product.price * qty
            selling_total = transaction.selling_price

            profit = selling_total - original_total

            if selling_total > 0:
                transaction.profit_percentage = round((profit / selling_total) * 100, 2)
            else:
                transaction.profit_percentage = 0


            if product.stock < qty:
                transaction_form.add_error("quantity", "Not enough stock!")
                return render(request, "accounts/customer_form.html", {
                    "customer_form": customer_form,
                    "transaction_form": transaction_form,
                    "no_products": no_products,
                    "product_stock_json": json.dumps(product_stock),
                })

            product.stock -= qty
            product.updated_at = timezone.now()
            product.save()

            transaction.save()
            return redirect("accounts:customer_list")

    return render(request, "accounts/customer_form.html", {
        "customer_form": customer_form,
        "transaction_form": transaction_form,
        "no_products": no_products,
        "product_stock_json": json.dumps(product_stock),
        "today": date.today(),
    })


def customer_accounts(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    transactions = customer.transactions.order_by('-date')

    mode = request.GET.get("mode", "add") 

    customer_date = customer.created_at



   
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
        'customer_date': customer_date,
        'transactions': transactions,
        'credits': credits_list,     
        'total_selling': total_selling,
        'total_advance': total_advance,
        'total_credit': total_credit,
        'balance': final_balance,
        'credit_form': credit_form,
        'mode': mode,
    }


    return render(request, 'accounts/customer_ledger.html', context)



@login_required
def customer_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    transactions = customer.transactions.order_by('-date')
    credits = customer.credits.order_by('-date')

    for t in transactions:
        t.row_balance = (t.selling_price or 0) - (t.advance_amount or 0)

    total_selling = transactions.aggregate(Sum('selling_price'))['selling_price__sum'] or 0
    total_advance = transactions.aggregate(Sum('advance_amount'))['advance_amount__sum'] or 0
    total_credit = credits.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_selling - total_advance - total_credit

    return render(request, "accounts/customer_view.html", {
        "customer": customer,
        "transactions": transactions,
        "credits": credits,
        "total_selling": total_selling,
        "total_advance": total_advance,
        "total_credit": total_credit,
        "balance": balance,
    })



from .models import Product

@login_required
def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name").strip()
        price = int(request.POST.get("price"))
        customer_price = int(request.POST.get("customer_price"))
        stock = int(request.POST.get("stock"))
        updated_at = request.POST.get("updated_at")

        #  INVESTED AMOUNT SET ONLY ONCE 
        invested_amount = price * stock

        Product.objects.create(
            user=request.user,
            name=name,
            price=price,
            customer_price=customer_price,
            stock=stock,
            invested_amount=invested_amount,  
            updated_at=updated_at
        )

        return redirect("accounts:product_list")

    return render(request, "accounts/add_product.html",{
        "today": date.today() 
    })







from .models import ProductStockHistory
from django.utils import timezone

def add_transaction(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)

        if form.is_valid():
            t = form.save(commit=False)
            if not t.date:
                t.date = timezone.now()
            t.customer = customer
            t.user = request.user

            product = form.cleaned_data["product"]
            qty = form.cleaned_data["quantity"]

            t.product = product
            t.product_name = product.name
            t.original_price = product.price
            t.customer_price = product.customer_price
            t.selling_price = product.customer_price * qty
            #  PROFIT PERCENTAGE
            original_total = product.price * qty
            selling_total = t.selling_price

            profit = selling_total - original_total

            if selling_total > 0:
                t.profit_percentage = round((profit / selling_total) * 100, 2)
            else:
                t.profit_percentage = 0



            #  STOCK LOGIC
            if product.stock >= qty:
                product.stock -= qty      
                product.updated_at = timezone.now()
                product.save()
            else:
                form.add_error("quantity", "Not enough stock")
                return render(request, "accounts/transaction_form.html", {
                    "form": form,
                    "customer": customer
                })

            t.save()
            return redirect("accounts:customer_ledger", customer.id)

    else:
        form = TransactionForm(user=request.user)

    return render(request, "accounts/transaction_form.html", {
        "form": form,
        "customer": customer
    })


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
                    Q(serial_no=query) |
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
        product_names = (
            cust.transactions
            .values_list("product_name", flat=True)
            .distinct()
        )
        product_names_str = ",".join(customer.phone for customer in customers)
        customer_data.append({
            'id': cust.id,
            'customer_id': cust.customer_id,
            'serial_no': cust.serial_no,
            'created_at': cust.created_at,
            'name': cust.name,
            'phone': cust.phone,
            'total_selling': total_selling,
            'total_paid': total_paid,
            'balance': balance,
            'is_due': cust.is_due,
            'customer_mode': cust.customer_mode,
            'products': product_names_str,
            
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
        form = CustomerEditForm(request.POST, instance=customer) 
        if form.is_valid():
            form.save()
            return redirect("accounts:customer_list")
    else:
        form = CustomerEditForm(instance=customer) 

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
        form = TransactionForm(
            request.POST,
            instance=transaction,
            user=request.user
        )

        if form.is_valid():
            updated_transaction = form.save(commit=False)

            new_product = form.cleaned_data.get("product")   
            new_quantity = form.cleaned_data.get("quantity")

            #  SAME PRODUCT 
            if old_product == new_product and new_product is not None:
                if new_quantity != old_quantity:
                    before = new_product.stock
                    after = before + old_quantity - new_quantity

                    new_product.stock = after
                    new_product.save()

                    ProductStockHistory.objects.create(
                        product=new_product,
                        stock_before=before,
                        stock_after=after
                    )

            # PRODUCT CHANGED 
            elif old_product != new_product:

                # RESTORE OLD PRODUCT 
                if old_product is not None:
                    old_before = old_product.stock
                    old_product.stock = old_before + old_quantity
                    old_product.save()

                    ProductStockHistory.objects.create(
                        product=old_product,
                        stock_before=old_before,
                        stock_after=old_product.stock
                    )

                # REDUCE NEW PRODUCT 
                if new_product is not None:
                    new_before = new_product.stock
                    new_product.stock = new_before - new_quantity
                    new_product.save()

                    ProductStockHistory.objects.create(
                        product=new_product,
                        stock_before=new_before,
                        stock_after=new_product.stock
                    )

            #  PROFIT % RECALC 
            original_total = (
                (updated_transaction.original_price or 0) *
                (updated_transaction.quantity or 1)
            )

            selling_total = updated_transaction.selling_price or 0
            profit = selling_total - original_total

            if selling_total > 0:
                updated_transaction.profit_percentage = round(
                    (profit / selling_total) * 100, 2
                )
            else:
                updated_transaction.profit_percentage = 0

            updated_transaction.save()
            return redirect("accounts:customer_ledger", customer.id)

    else:
        form = TransactionForm(
            instance=transaction,
            user=request.user
        )

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



@login_required
def turnover_page(request):

    # define year FIRST
    today = datetime.today()
    month = today.month
    year = today.year

    #  rebuild turnover tables
    save_monthly_turnover(request.user)
    save_yearly_product_turnover(request.user)

    customers = Customer.objects.filter(user=request.user)

     #  DATE RANGE TURNOVER 
   

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    range_total_sold = 0
    range_total_paid = 0
    range_balance = 0

    if from_date and to_date:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

        # SOLD (transaction date)
        range_transactions = Transaction.objects.filter(
            customer__in=customers,
            date__date__range=(from_dt, to_dt)
        )

        range_total_sold = range_transactions.aggregate(
            total=Sum("selling_price")
        )["total"] or 0

        #  ADVANCE PAID (transaction date based)
        range_advance_paid = range_transactions.aggregate(
            total=Sum("advance_amount")
        )["total"] or 0

        # CREDIT PAID (credit date based)
        range_credit_paid = Credit.objects.filter(
            customer__in=customers,
            date__date__range=(from_dt, to_dt)
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        #  TOTAL PAID
        range_total_paid = range_advance_paid + range_credit_paid

        range_balance = range_total_sold - range_total_paid

    #  PRODUCT YEARLY TURNOVER (NOW year exists)
    product_turnover = ProductYearlyTurnover.objects.filter(
        user=request.user,
        year=year
    ).first()

    # TOTAL TURNOVER
    total_sold = Transaction.objects.filter(
        customer__in=customers
    ).aggregate(total=Sum('selling_price'))['total'] or 0

    total_advance = Transaction.objects.filter(
        customer__in=customers
    ).aggregate(total=Sum('advance_amount'))['total'] or 0

    total_credit = Credit.objects.filter(
        customer__in=customers
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_paid = total_advance + total_credit
    total_balance = total_sold - total_paid

    # BALANCE STOCK COST 
    balance_stock_cost = Product.objects.filter(
        user=request.user
    ).aggregate(
        total=Sum(
            F("stock") * F("price")
        )
    )["total"] or 0

    # MONTHLY
    try:
        record = MonthlyTurnover.objects.get(
            month=month,
            year=year,
            user=request.user
        )
        monthly_sold = record.sold
        monthly_paid = record.paid
        monthly_balance = record.balance
        monthly_profit = record.profit
        monthly_original_cost = record.original_cost
    except MonthlyTurnover.DoesNotExist:
        monthly_sold = monthly_paid = monthly_balance = monthly_profit = monthly_original_cost = 0

    months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    records = MonthlyTurnover.objects.filter(year=year, user=request.user)
    rec_dict = {r.month: r for r in records}

    monthly_data = []
    for m in range(1, 13):
        r = rec_dict.get(m)
        monthly_data.append({
            "month": months[m-1],
            "sold": r.sold if r else 0,
            "original_cost": r.original_cost if r else 0,
            "profit": r.profit if r else 0,
            "paid": r.paid if r else 0,
            "balance": r.balance if r else 0,
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

      
        "product_turnover": product_turnover,
        "year": year,
        "balance_stock_cost": balance_stock_cost,
        "from_date": from_date,
        "to_date": to_date,

        "range_total_sold": range_total_sold,
        "range_total_paid": range_total_paid,
        "range_balance": range_balance,
        "year": year,
        "today": date.today().isoformat(), 

    })





def save_monthly_turnover(user):
    from django.db.models import Sum
    from datetime import datetime

    now = datetime.now()
    year = now.year

   
    MonthlyTurnover.objects.filter(user=user, year=year).delete()

    customers = Customer.objects.filter(user=user)

    for month in range(1, 13):

        # TRANSACTIONS 
        trans = Transaction.objects.filter(
            customer__in=customers,
            date__year=year,
            date__month=month
        )

        # PAYMENTS (ONLY THIS MONTH) 
        credits = Credit.objects.filter(
            customer__in=customers,
            date__year=year,
            date__month=month
        )

        # SOLD 
        sold = trans.aggregate(
            total=Sum("selling_price")
        )["total"] or 0

        #  PAID 
        advance_paid = trans.aggregate(
            total=Sum("advance_amount")
        )["total"] or 0

        credit_paid = credits.aggregate(
            total=Sum("amount")
        )["total"] or 0

        paid = advance_paid + credit_paid

        #  ORIGINAL COST & PROFIT 
        original_cost = 0
        for t in trans:
            cost = (t.original_price or 0) * (t.quantity or 1)
            original_cost += cost

        profit = sold - original_cost

        # BALANCE 
        balance = sold - paid

        # SAVE 
        MonthlyTurnover.objects.create(
            user=user,
            month=month,
            year=year,
            sold=sold,
            original_cost=original_cost,
            profit=profit,
            paid=paid,
            balance=balance
        )




from accounts.models import Customer, CompanyDetails

def export_customer_pdf(request, customer_id):
    
    company = CompanyDetails.objects.filter(user=request.user).first()
    customer = get_object_or_404(Customer, pk=customer_id)
    transactions = customer.transactions.all()
    credits = customer.credits.all()

    response = HttpResponse(content_type='application/pdf')
    filename = f"{customer.name}_ledger.pdf"
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    
    font_path = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans-Bold.ttf")))


    
    pdf.setStrokeColorRGB(0, 0, 0)
    pdf.setLineWidth(2)
    pdf.rect(20, 20, width - 40, height - 40)

   

    y = height - 60

    
    logo_path = os.path.join(settings.STATIC_ROOT, "accounts", "logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 40, y - 70, width=90, height=90)

    
    pdf.setFont("DejaVuSans-Bold", 24)

    company_name = company.company_name if company else "Company Name"
    pdf.drawString(150, y, company_name)

    pdf.setFont("DejaVuSans", 12)

    # Phone 
    phone = customer.phone if customer.phone else ""
    pdf.drawString(150, y - 20, f"Phone: {phone}")

    # Address
    address = company.address if company else ""
    pdf.drawString(150, y - 40, f"Address: {address}")
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

    
    stamp_path = os.path.join(settings.STATIC_ROOT, "accounts", "stamp.jpg")

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
    footer_company = company.company_name if company else ""
    pdf.drawString(40, footer_y, f"{footer_company} © 2025")

    pdf.drawString(
        40,
        footer_y - 12,
        "Thank you for your business!"
    )

    pdf.showPage()
    pdf.save()
    return response


from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from django.db.models import Sum
import os

from .models import Customer


def export_customer_list_pdf(request):
    customers = Customer.objects.filter(user=request.user)
    company = CompanyDetails.objects.filter(user=request.user).first()

    completed_only = request.GET.get("completed")


    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Customer_List.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # FONTS 
    font_regular = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans.ttf")
    font_bold = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans-Bold.ttf")

    pdfmetrics.registerFont(TTFont("DejaVu", font_regular))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_bold))

    #PAGE BORDER
    border_margin = 20
    pdf.setLineWidth(2)
    pdf.rect(
        border_margin,
        border_margin,
        width - (border_margin * 2),
        height - (border_margin * 2),
    )

    
    #  HEADER
    header_top = height - 70

    logo_path = os.path.join(settings.STATIC_ROOT, "accounts", "logo.png")
    logo_size = 100

    if os.path.exists(logo_path):
        pdf.drawImage(
            ImageReader(logo_path),
            border_margin + 10,
            header_top - logo_size + 30,
            width=logo_size,
            height=logo_size,
            mask="auto"
        )

    pdf.setFont("DejaVu-Bold", 20)
    company_name = company.company_name if company else "Company Name"
    pdf.drawCentredString(width / 2, header_top, company_name)

    pdf.setFont("DejaVu", 11)

    # Phone 
    phone = customers.first().phone if customers.exists() else ""
    pdf.drawCentredString(width / 2, header_top - 22, f"Phone: {phone}")

    # Address – company address
    address = company.address if company else ""
    pdf.drawCentredString(
        width / 2,
        header_top - 38,
        f"Address: {address}"
    )

    
    y = header_top - 2



    #  TABLE START Y 
    y -= 160

    # TABLE DATA 
    styles = getSampleStyleSheet()

    def build_table(font_size):
        normal = styles["Normal"]
        normal.fontName = "DejaVu"
        normal.fontSize = font_size

        table_data = [[
            "S.No", "Customer ID", "Date",
            "Name", "Phone", "Products",
            "Total Amount", "Paid", "Balance"
        ]]

        sno = 1

        for c in customers:
            total_selling = c.transactions.aggregate(
                total=Sum("selling_price")
            )["total"] or 0

            total_advance = c.transactions.aggregate(
                total=Sum("advance_amount")
            )["total"] or 0

            total_credit = c.credits.aggregate(
                total=Sum("amount")
            )["total"] or 0

            total_paid = total_advance + total_credit
            balance = total_selling - total_paid

            if completed_only:
                # completed customers only (balance = 0)
                if balance != 0:
                    continue
            else:
                # normal list (due customers only)
                if balance <= 0:
                    continue

            products = ", ".join(
                filter(
                    None,
                    c.transactions.values_list("product_name", flat=True)
                )
            )

            table_data.append([
                sno,
                f"{c.serial_no:03d}",
                c.created_at.strftime("%d-%m-%Y") if c.created_at else "",
                Paragraph(c.name, normal),
                c.phone,
                Paragraph(products, normal),
                f"₹ {total_selling}",
                f"₹ {total_paid}",
                f"₹ {balance}",
            ])

            sno += 1

        col_widths = [
            28,   # S.No
            64,   # Customer ID
            55,   # Date
            85,   # Name  
            63,   # Phone
            95,   # Products 
            56,   # Total Amount
            50,   # Paid
            50,   # Balance 
        ]


        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),

            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (2, -1), "CENTER"),
            ("ALIGN", (6, 1), (-1, -1), "RIGHT"),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        return table, table_data

    # AUTO FONT REDUCE
    max_width = width - (border_margin * 2) - 10

    for fs in [9, 8, 7]:
        table, table_data = build_table(fs)
        tw, th = table.wrap(0, 0)
        if tw <= max_width:
            break

    #  DRAW TABLE 
    x = border_margin + 5
    table_height = len(table_data) * (fs + 9)

    table.drawOn(pdf, x, y - table_height)

    pdf.showPage()
    pdf.save()
    return response


from .models import ProductBrand
from django.db import IntegrityError
@login_required
def product_brands(request):
    brands = ProductBrand.objects.filter(user=request.user).order_by("name")

    if request.method == "POST":
        raw_name = request.POST.get("brand_name", "")

        # Normalize
        name = " ".join(raw_name.strip().split()).title()

        if not name:
            messages.error(request, "❌ Brand name cannot be empty")
            return redirect("accounts:product_brands")

        try:
            brand, created = ProductBrand.objects.get_or_create(
                user=request.user,
                name=name
            )

            if not created:
                messages.error(request, "❌ Brand already exists")
            else:
                messages.success(request, "✅ Brand added successfully")

        except IntegrityError:
            messages.error(request, "❌ Brand already exists")

        return redirect("accounts:product_brands")

    return render(request, "accounts/product_brands.html", {
        "brands": brands
    })
@login_required
def edit_product_brand(request, pk):
    brand = get_object_or_404(ProductBrand, pk=pk, user=request.user)

    if request.method == "POST":
        raw_name = request.POST.get("brand_name", "")
        name = " ".join(raw_name.strip().split()).title()

        if not name:
            messages.error(request, "Brand name cannot be empty")
            return redirect("accounts:edit_product_brand", pk=pk)

        if ProductBrand.objects.filter(
            user=request.user,
            name=name
        ).exclude(pk=pk).exists():
            messages.error(request, "Brand already exists")
            return redirect("accounts:edit_product_brand", pk=pk)

        brand.name = name
        brand.save()
        messages.success(request, "Brand updated successfully")
        return redirect("accounts:product_brands")

    return render(request, "accounts/edit_product_brand.html", {
        "brand": brand
    })


@login_required
def delete_product_brand(request, brand_id):
    brand = get_object_or_404(ProductBrand, id=brand_id, user=request.user)
    brand.delete()
    return redirect("accounts:product_brands")





from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import os

from .models import Product


def export_product_list_pdf(request):
    products = Product.objects.filter(user=request.user)
    company = CompanyDetails.objects.filter(user=request.user).first()
    first_customer = Customer.objects.filter(user=request.user).first()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Product_Stock_List.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    #  FONTS 
    font_regular = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans.ttf")
    font_bold = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans-Bold.ttf")

    pdfmetrics.registerFont(TTFont("DejaVu", font_regular))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_bold))

    #  PAGE BORDER 
    border_margin = 20
    pdf.setLineWidth(2)
    pdf.rect(
        border_margin,
        border_margin,
        width - (border_margin * 2),
        height - (border_margin * 2),
    )

    # HEADER 
    header_top = height - 70

    logo_path = os.path.join(settings.STATIC_ROOT, "accounts", "logo.png")
    logo_size = 100

    if os.path.exists(logo_path):
        pdf.drawImage(
            ImageReader(logo_path),
            border_margin + 10,
            header_top - logo_size + 30,
            width=logo_size,
            height=logo_size,
            mask="auto"
        )

    pdf.setFont("DejaVu-Bold", 20)
    company_name = company.company_name if company else "Company Name"
    pdf.drawCentredString(width / 2, header_top, company_name)

    pdf.setFont("DejaVu", 11)

    # Phone 
    phone = first_customer.phone if first_customer else ""
    pdf.drawCentredString(width / 2, header_top - 22, f"Phone: {phone}")

    # Address 
    address = company.address if company else ""
    pdf.drawCentredString(
        width / 2,
        header_top - 38,
        address
    )


    # TITLE 
    pdf.setFont("DejaVu-Bold", 14)
    pdf.drawCentredString(width / 2, header_top - 115, "PRODUCT STOCK LIST")

    # TABLE START 
    y = header_top - 140

    table_data = [
        ["Product Name", "Stock", "Original Price"]
    ]

    for p in products:
        table_data.append([
            p.name,
            str(p.stock),
            f"₹ {p.price}",
        ])

    col_widths = [
        260,  # Product Name
        100,  # Stock
        120,  # Original Price
    ]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),

        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    table_width, table_height = table.wrap(0, 0)
    x = (width - table_width) / 2

    table.drawOn(pdf, x, y - table_height)

    pdf.showPage()
    pdf.save()
    return response



