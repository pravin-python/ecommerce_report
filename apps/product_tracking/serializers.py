from rest_framework import serializers
from apps.product_tracking.models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    food_category_display = serializers.SerializerMethodField()
    exempted_reason_display = serializers.SerializerMethodField()
    diet_display = serializers.SerializerMethodField()
    grade_in_display = serializers.SerializerMethodField()
    processing_level_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    sync_status_display = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'barcode', 'brand_id', 'brand', 'company_id', 'company',
            'category', 'food_category', 'food_category_display',
            'exempted_reason', 'exempted_reason_display',
            'diet', 'diet_display', 'description', 'ingredients', 'nutrients', 'allergens',
            'tag_1', 'tag_2', 'tag_3', 'tag_4', 'tag_5',
            'images', 'score_in', 'grade_in', 'grade_in_display',
            'serving_size_scores', 'package_type', 'net_weight', 'gross_weight',
            'net_content', 'mass_measurement_unit', 'fssai_lic', 'country_of_origin',
            'processing_level', 'processing_level_display',
            'status', 'status_display', 'sync_status', 'sync_status_display',
            'synced_at', 'created_at', 'updated_at'
        ]

    def get_food_category_display(self, obj):
        return obj.get_food_category_display() if obj.food_category else None

    def get_exempted_reason_display(self, obj):
        return obj.get_exempted_reason_display() if obj.exempted_reason else None

    def get_diet_display(self, obj):
        return obj.get_diet_display() if obj.diet else None

    def get_grade_in_display(self, obj):
        return obj.get_grade_in_display() if obj.grade_in else None

    def get_processing_level_display(self, obj):
        return obj.get_processing_level_display() if obj.processing_level else None

    def get_status_display(self, obj):
        return obj.get_status_display() if obj.status else None

    def get_sync_status_display(self, obj):
        return obj.get_sync_status_display() if obj.sync_status else None
