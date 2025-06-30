from django.db import models
from apps.customer_info.models import *

class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name='children',
        db_column='parent_id'
    )

    class Meta:
        managed = False
        db_table = 'categories'

    def __str__(self):
        return self.name
    
class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=500)
    barcode = models.CharField(max_length=25, null=True, blank=True)
    brand_id = models.BigIntegerField(null=True, blank=True)
    # category_id = models.BigIntegerField(null=True, blank=True)

    FOOD_CATEGORY_CHOICES = [
        ('solid', 'Solid'),
        ('liquid', 'Liquid'),
        ('exempted', 'Exempted'),
    ]
    food_category = models.CharField(max_length=10, choices=FOOD_CATEGORY_CHOICES, null=True, blank=True)

    EXEMPTED_REASON_CHOICES = [
        ('Natural form/Pure form', 'Natural form/Pure form'),
        ('Liquor', 'Liquor'),
        ('Herbs and Medicine without sugar', 'Herbs and Medicine without sugar'),
        ('Other', 'Other'),
    ]
    exempted_reason = models.CharField(max_length=50, choices=EXEMPTED_REASON_CHOICES, null=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column='category_id',
        related_name='products' 
    )

    brand = models.CharField(max_length=255, null=True, blank=True)
    company_id = models.BigIntegerField(null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)

    DIET_CHOICES = [
        ('vg', 'Vegetarian'),
        ('nvg', 'Non-Vegetarian'),
        ('vgn', 'Vegan'),
    ]
    diet = models.CharField(max_length=3, choices=DIET_CHOICES, null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    ingredients = models.TextField(null=True, blank=True)
    nutrients = models.TextField(null=True, blank=True)
    allergens = models.TextField(null=True, blank=True)

    tag_1 = models.CharField(max_length=255, null=True, blank=True)
    tag_2 = models.CharField(max_length=255, null=True, blank=True)
    tag_3 = models.CharField(max_length=255, null=True, blank=True)
    tag_4 = models.CharField(max_length=255, null=True, blank=True)
    tag_5 = models.CharField(max_length=255, null=True, blank=True)

    images = models.TextField(null=True, blank=True)
    score_in = models.SmallIntegerField(null=True, blank=True)

    GRADE_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ]
    grade_in = models.CharField(max_length=1, choices=GRADE_CHOICES, null=True, blank=True)

    serving_size_scores = models.JSONField(null=True, blank=True)
    package_type = models.CharField(max_length=255, null=True, blank=True)
    net_weight = models.CharField(max_length=25, null=True, blank=True)
    gross_weight = models.CharField(max_length=15, null=True, blank=True)
    net_content = models.CharField(max_length=255, null=True, blank=True)
    mass_measurement_unit = models.CharField(max_length=255, null=True, blank=True)
    fssai_lic = models.TextField(null=True, blank=True)
    country_of_origin = models.TextField(null=True, blank=True)

    PROCESSING_LEVEL_CHOICES = [
        ('Unprocessed or Natural foods and Minimally Processed', 'Unprocessed or Natural foods and Minimally Processed'),
        ('Processed Culinary Ingredients', 'Processed Culinary Ingredients'),
        ('Processed foods', 'Processed foods'),
        ('Ultra-processed foods', 'Ultra-processed foods'),
    ]
    processing_level = models.CharField(max_length=100, choices=PROCESSING_LEVEL_CHOICES, null=True, blank=True)

    STATUS_CHOICES = [
        ('raw', 'Raw'),
        ('enable', 'Enable'),
        ('disable', 'Disable'),
        ('deficient', 'Deficient'),
        ('exempted', 'Exempted'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='raw')

    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ]
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='pending')

    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'products'
        managed = False
        
class Metafield(models.Model):
    TYPE_CHOICES = [
        ('Allergy', 'Allergy'),
        ('Report', 'Report'),
        ('Product_not_found', 'Product_not_found'),
    ]

    id = models.BigAutoField(primary_key=True)
    customer_id = models.BigIntegerField()
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column='product_id',
        related_name='metafields'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'metafields'
        managed = False