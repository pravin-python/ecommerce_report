from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated

from django.utils.timezone import now as timezone_now
from datetime import timedelta

from django.db.models import Count, Q
from apps.pages.models import URLRecord
from apps.product_tracking.models import Product
from apps.pages.models import DashboardComponent
from apps.customer_info.models import CustomerHistory, Customer

from apps.pages.serializers.page_serializers import URLRecordSerializer

class PagesViewSet(viewsets.ModelViewSet):
    queryset = URLRecord.objects.all()
    serializer_class = URLRecordSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=False, methods=['get'], url_path='search')
    def search_show_name(self, request):
        """
        Search URL records by show_name query param.
        Example: /api/pages/search/?q=dashboard
        """
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({"detail": "Query param 'q' is required."}, status=400)

        results = URLRecord.objects.filter(show_name__icontains=query).order_by('-show_name').values('url_pattern', 'show_name')

        data = list(results)

        response_data = {
            "total_records": len(data),
            "data": data
        }

        return Response(response_data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/info')
    def dashboard_info(self, request):
        now = timezone_now()
        products_qs = Product.objects.all()
        customer_qs = Customer.objects.all()
        dashboard_components = DashboardComponent.objects.all().order_by('position')
        customer_history_qs = CustomerHistory.objects.all()

        product_counts = products_qs.aggregate(
            total=Count('id'),
            enabled=Count('id', filter=Q(status='enable')),
            exempted=Count('id', filter=Q(status='exempted'))
        )

        customer_counts = customer_qs.aggregate(
            total=Count('id'),
            enabled=Count('id', filter=Q(is_guest=False)),
            guest=Count('id', filter=Q(is_guest=True))
        )

        history_counts = customer_history_qs.aggregate(
            this_month=Count('id', filter=Q(updated_at__year=now.year, updated_at__month=now.month)),
            today=Count('id', filter=Q(updated_at__date=now.date())),
            yesterday=Count('id', filter=Q(updated_at__date=now.date() - timedelta(days=1)))
        )

        response_data = {
            'total_products': product_counts['total'],
            'enabled_products_count': product_counts['enabled'],
            'exempted_products_count': product_counts['exempted'],
            'total_customers': customer_counts['total'],
            'enabled_customers_count': customer_counts['enabled'],
            'guest_customers_count': customer_counts['guest'],
            'month_customers': history_counts['this_month'],
            'today_customers': history_counts['today'],
            'yesterday_customers': history_counts['yesterday'],
            "dashboard_components": dashboard_components,
        }

        return Response(response_data)