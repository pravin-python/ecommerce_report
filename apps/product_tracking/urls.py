from django.urls import path
from apps.product_tracking import views 

urlpatterns = [
    path('most-scanned-categories/', views.scanned_categories, name="most_scanned_categories"),
    path('most-scanned-categories/child-category/<int:parent_id>/', views.child_category_detail, name='child_category_detail'),
    path('most-scanned-products', views.most_scanned_products, name='most_scanned_products'),
    path('most-viewed-products', views.most_viewed_products, name='most_viewed_products'),
    path('product-not-found', views.product_not_found, name='product_not_found'),
    path('product-not-found/<int:customer_id>/', views.product_not_found_by_customer, name='product_not_found_by_customer'),
    path('', views.products, name='products'),
]
