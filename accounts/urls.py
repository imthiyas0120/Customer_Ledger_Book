from django.urls import path
from . import views
from .views import test_email

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/add/', views.customer_add, name='customer_add'),
    path('customer/<int:customer_id>/', views.customer_accounts, name='customer_ledger'),
    path('customer/<int:customer_id>/add_transaction/', views.add_transaction, name='add_transaction'),
    path('customer/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('customer/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    path('customer/<int:customer_id>/add_credit/', views.add_credit, name='add_credit'),
    path('search/', views.search_customers, name="search_customers"),
    path('customer/<int:customer_id>/export_pdf/', views.export_customer_pdf, name='export_customer_pdf'),
    path('credit/<int:credit_id>/edit/', views.credit_edit, name='credit_edit'),
    path('transaction/<int:transaction_id>/edit/', views.transaction_edit, name='transaction_edit'),
    path('customer/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('credit/<int:credit_id>/delete/', views.credit_delete, name='credit_delete'),
    path('transaction/<int:transaction_id>/delete/', views.transaction_delete, name='transaction_delete'),
    path('turnover/', views.turnover_page, name="turnover"),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path("product/<int:product_id>/view/", views.product_view, name="product_view"),
    path('calculator/', views.calculator_view, name='calculator'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.home, name='profile'),
    path("test-email/", test_email, name="test_email"),
    path('get-product-price/<int:product_id>/', views.get_product_price, name='get_product_price'),
    path("forgot/", views.forgot_password, name="forgot_password"),
    path("security-check/", views.reset_password, name="reset_password"),
    path("set-password/", views.save_new_password, name="save_new_password"),
    path("products/details/", views.product_details, name="product_details"),
    path("product-variant/edit/<int:pk>/", views.edit_product_variant, name="edit_product_variant"),
    path("product-variant/delete/<int:pk>/", views.delete_product_variant, name="delete_product_variant"),
    path('product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path("forgot/", views.forgot_password, name="forgot_password"),
    path("signup/", views.signup, name="signup"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("forgot-username/", views.forgot_username, name="forgot_username"),
    path('customer/<int:customer_id>/view/', views.customer_view, name='customer_view'),
    path("customers/download/",views.export_customer_list_pdf,name="export_customer_list_pdf"),
    path("product-brands/", views.product_brands, name="product_brands"),
    path("product-brands/edit/<int:pk>/", views.edit_product_brand, name="edit_product_brand"),
    path("product-brands/delete/<int:brand_id>/",views.delete_product_brand,name="delete_product_brand"),
    path("products/download-stocks-pdf/",views.export_product_list_pdf,name="export_product_list_pdf"),
    path("user-details/", views.user_details, name="user_details"),
    path("company-details/", views.company_details, name="company_details"),
    path("products/add-stock/", views.add_stock, name="add_stock"),







]
