from django.db import models
from apps.product_tracking.models import *


class Customer(models.Model):
    id = models.BigAutoField(primary_key=True)
    device_token = models.CharField(max_length=255, null=True, blank=True)
    provider_id = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    is_dummy_email = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    DIET_CHOICES = [
        ('vg', 'Vegetarian'),
        ('nvg', 'Non-Vegetarian'),
        ('vgn', 'Vegan'),
    ]
    diet = models.CharField(max_length=3, choices=DIET_CHOICES, null=True, blank=True)
    
    image = models.CharField(max_length=255, null=True, blank=True)
    is_notification = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=255, null=True, blank=True)
    referred_by = models.BigIntegerField(null=True, blank=True)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('waiting', 'Waiting'),
        ('fraud', 'Fraud'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    remember_token = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customers'  # exact table name
        managed = False  


class CustomerHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column='customer_id',
        on_delete=models.DO_NOTHING
    )
    
    product = models.ForeignKey(
        Product,
        db_column='product_id',
        on_delete=models.DO_NOTHING
    )
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'customer_histories'
        managed = False

class CustomerList(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column='customer_id')
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'customer_lists'
        managed = False
        
class CustomerListItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer_list = models.ForeignKey(CustomerList, on_delete=models.DO_NOTHING, db_column='customer_list_id')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, db_column='product_id')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'customer_list_items'
        managed = False

class Point(models.Model):
    POINT_TYPE_CHOICES = [
        ('product_upload', 'Product Upload'),
        ('product_review', 'Product Review'),
        ('product_scan', 'Product Scan'),
        ('product_share', 'Product Share'),
        ('profile_completion', 'Profile Completion'),
        ('app_referral', 'App Referral'),
        ('referred_by', 'Referred By'),
    ]

    id = models.BigAutoField(primary_key=True)
    
    customer = models.ForeignKey(
        Customer, 
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_column='customer_id'
    )

    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_column='product_id'
    )

    point_type = models.CharField(
        max_length=30,
        choices=POINT_TYPE_CHOICES,
        null=True,
        blank=True
    )

    ref_customer = models.BigIntegerField(null=True, blank=True)

    points = models.BigIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'points'
        managed = False
        
class CustomerUpload(models.Model):
    CONTRIBUTION_TYPE_CHOICES = [
        ('upload', 'Upload'),
        ('contribute', 'Contribute'),
    ]

    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('review', 'Review'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.BigAutoField(primary_key=True)
    raw_product_id = models.BigIntegerField(null=True, blank=True)
    customer_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)
    net_weight = models.CharField(max_length=255, null=True, blank=True)
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    brand_id = models.BigIntegerField(null=True, blank=True)
    contribution_type = models.CharField(
        max_length=10,
        choices=CONTRIBUTION_TYPE_CHOICES,
        default='upload'
    )
    front_img = models.CharField(max_length=255)
    back_img = models.CharField(max_length=255, null=True, blank=True)
    ingredients_img = models.CharField(max_length=255, null=True, blank=True)
    nutrients_img = models.CharField(max_length=255, null=True, blank=True)
    barcode_img = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='review'
    )
    managed_by = models.BigIntegerField(null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    points = models.IntegerField(default=0)
    point_collection = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customer_uploads'
        managed = False
        
class ProductReview(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column='customer_id',
        on_delete=models.DO_NOTHING
    )
    product = models.ForeignKey(
        Product,
        db_column='product_id',
        on_delete=models.DO_NOTHING
    )
    review = models.TextField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    update_request = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='processing'
    )
    reason = models.CharField(max_length=255, null=True, blank=True)
    managed_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'product_reviews'
        managed = False