from django.urls import path

from apps.customer_info import views

urlpatterns = [
    path('', views.get_customer, name="customer"),
    path('referred/<int:referrer_id>/', views.customer_referred_list, name='customer_referred_list'),
    path('list-items/', views.customer_list_items, name="customer_list_items"),
    path('list-items/<int:list_id>/', views.customer_list_detail, name='customer_list_detail'),
    path('scan-history', views.scan_history, name='customer_scanned_products'),
    path('leaderboard', views.customer_points, name='leaderboard'),
    path('referred/', views.referred_by_customer, name="referred_by_customer"),
    path('customer-product-reviews/', views.customer_product_reviews, name="customer_product_reviews"),
    path('product-problem-report/', views.product_problem_report, name="product_problem_report"),
    path('customer-uploads-products/', views.customer_uploads_products, name="customer_uploads_products"),
    path('customer-uploads/<int:customer_id>/', views.customer_product_details, name='customer_product_details'),
    path('customer-allergies-lists/', views.customer_allergies_lists, name="customer_allergies_lists"),
]
