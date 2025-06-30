from rest_framework import serializers
from apps.customer_info.models import *
from apps.product_tracking.models import Product


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerHistorySerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CustomerHistory
        fields = '__all__'


class CustomerListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = CustomerList
        fields = '__all__'


class CustomerListItemSerializer(serializers.ModelSerializer):
    customer_list = CustomerListSerializer()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CustomerListItem
        fields = '__all__'


class PointSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Point
        fields = '__all__'
