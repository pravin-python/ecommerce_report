from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta

from apps.customer_info.models import *
from apps.product_tracking.models import Product
from apps.product_tracking.serializers import ProductSerializer, CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=False, methods=['get'], url_path='most-scan/table', name='most-scan-products-table')
    def most_top_10_scan_products_table(self, request):
        scanned_data = (
            CustomerHistory.objects
            .values('product_id')
            .annotate(scan_count=Count('id'))
            .filter(scan_count__gte=20)
            .order_by('-scan_count')[:10]
        )

        product_ids = [item['product_id'] for item in scanned_data]
        product_map = {product.id: product for product in Product.objects.filter(id__in=product_ids)}

        result = []
        for item in scanned_data:
            product = product_map.get(item['product_id'])
            if product:
                result.append({
                    'product_name': product.name,
                    'barcode': product.barcode,
                    'score_grade': f"{product.score_in} ({product.grade_in})" if product.score_in is not None else None,
                    'count': item['scan_count']
                })

        return Response({
            "total_records": len(result),
            "data": result
        })
    
    @action(detail=False, methods=['get'], url_path='grade-summary/chart', name='product-grade-summary-chart')
    def product_grade_summary_chart(self, request):
        """
        Returns the count of products by their grade_in (A, B, C, D, etc.)
        """
        grade_counts = (
            Product.objects
            .exclude(grade_in__isnull=True)
            .values('grade_in')
            .annotate(count=Count('id'))
            .order_by('grade_in')
        )

        result = [
            {'label': item['grade_in'], 'grade': item['count']}
            for item in grade_counts
        ]


        return Response({
            "total_records": len(result),
            "data": result
        })
    
    @action(detail=False, methods=['get'], url_path='status-summary/chart', name='product-status-summary-chart')
    def product_status_summary_chart(self, request):
        """
        Returns the count of products by their status 
        """
        STATUS_DICT = dict(Product.STATUS_CHOICES)
        grade_counts = (
            Product.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        result = [
            {
                'label': STATUS_DICT.get(item['status'], item['status']),  # Use display label
                'status': item['count']
            }
            for item in grade_counts
        ]

        return Response({
            "total_records": len(result),
            "data": result
        })