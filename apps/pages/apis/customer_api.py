from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated

from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from calendar import monthrange
from django.utils import timezone


from apps.customer_info.models import *
from apps.product_tracking.models import Product
from apps.customer_info.serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=False, methods=['get'], url_path='table', name='last-10-customers')
    def customers_table(self, request):
        """
        Return last 10 customers based on type (guest or registered).
        Default: registered
        """
        customer_type = request.GET.get('filter', 'registered').lower()
        data = []
        if customer_type == 'guest':
            queryset = Customer.objects.filter(is_guest=True)
            queryset = queryset.order_by('-created_at')[:10]
            for record in queryset:
                data.append({
                    'customer_name': record.name or "GUEST",
                    'customer_status': record.status,
                   'date': record.created_at.strftime('%d-%m-%Y %I:%M %p'),
                })
        else:
            queryset = Customer.objects.filter(is_guest=False)
            queryset = queryset.order_by('-created_at')[:15]
            for record in queryset:
                data.append({
                    'customer_name': record.name,
                    'customer_mobile': record.mobile or "-",
                    'customer_email': record.email or "-",
                    'customer_status': record.status,
                    'date': record.created_at.strftime('%d-%m-%Y %I:%M %p'),
                })

        response_data = {
            "total_records": len(data),
            "data": data
        }

        return Response(response_data)
    

    @action(detail=False, methods=['get'], url_path='scan-summary/table', name='scan-summary-table')
    def customer_scan_summary_table(self, request):
        """Returns the last 10 customer history records"""
        customer_history_qs = CustomerHistory.objects.select_related('customer', 'product').order_by('-id')[:10]

        data = []
        for record in customer_history_qs:
            data.append({
                'customer_name': record.customer.name,
                'product_name': record.product.name,
                'barcode': record.product.barcode,
                'score_grade': f"{record.product.score_in} ({record.product.grade_in})",
                'date':  record.updated_at.strftime('%d-%m-%Y %I:%M %p'),
            })

        response_data = {
            "total_records": len(data),
            "data": data
        }

        return Response(response_data)
    
    @action(detail=False, methods=['get'], url_path='chart', name='customers-chart')
    def customers_chart(self, request):
        today = datetime.today().date()
        filter_type = request.GET.get('filter', 'month') or 'month'
        daily_stats = []

        if filter_type == 'daily':
            start_date = today - timedelta(days=6)

            qs = (
                Customer.objects
                .filter(created_at__date__gte=start_date)
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(
                    registered=Count('id', filter=Q(is_guest=False)),
                    guest=Count('id', filter=Q(is_guest=True)),
                )
                .order_by('day')
            )

            # Create a map {date: {registered, guest}}
            data_map = {entry['day']: entry for entry in qs}

            daily_stats = []
            for i in range(7):
                date = start_date + timedelta(days=i)
                data = data_map.get(date, {})
                daily_stats.append({
                    'label': date.strftime('%d-%m-%y'),
                    'registered': data.get('registered', 0),
                    'guest': data.get('guest', 0),
                })

        elif filter_type == 'week':
            last_monday = today - timedelta(days=today.weekday())
            start_date = last_monday - timedelta(weeks=6)  # Last 7 weeks including this one

            qs = (
                Customer.objects
                .filter(created_at__date__gte=start_date)
                .annotate(week=TruncWeek('created_at'))
                .values('week')
                .annotate(
                    registered=Count('id', filter=Q(is_guest=False)),
                    guest=Count('id', filter=Q(is_guest=True))
                )
                .order_by('week')
            )

            data_map = {item['week'].date(): item for item in qs}

            for i in range(7):
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(days=6)
                item = data_map.get(week_start, {})
                label = f"From {week_start.strftime('%d-%m-%Y')} To {week_end.strftime('%d-%m-%Y')}"
                daily_stats.append({
                    'label': label,
                    'registered': item.get('registered', 0),
                    'guest': item.get('guest', 0),
                })

        elif filter_type == 'month':
            start_month = today.replace(day=1)
            for _ in range(5):
                if start_month.month == 1:
                    start_month = start_month.replace(year=start_month.year - 1, month=12)
                else:
                    start_month = start_month.replace(month=start_month.month - 1)

            qs = (
                Customer.objects
                .filter(created_at__date__gte=start_month)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(
                    registered=Count('id', filter=Q(is_guest=False)),
                    guest=Count('id', filter=Q(is_guest=True))
                )
                .order_by('month')
            )

            data_map = {item['month'].date(): item for item in qs}
            current = start_month

            for _ in range(6):
                label_key = current
                item = data_map.get(label_key, {})
                daily_stats.append({
                    'label': current.strftime('%b %Y'),
                    'registered': item.get('registered', 0),
                    'guest': item.get('guest', 0),
                })

                # Safely increment month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
                current = current.replace(day=1)

        elif filter_type == 'year':
            start_year = today.year - 4
            start_date = datetime(start_year, 1, 1).date()

            qs = (
                Customer.objects
                .filter(created_at__date__gte=start_date)
                .annotate(year=TruncYear('created_at'))
                .values('year')
                .annotate(
                    registered=Count('id', filter=Q(is_guest=False)),
                    guest=Count('id', filter=Q(is_guest=True))
                )
                .order_by('year')
            )

            data_map = {item['year'].year: item for item in qs}
            for i in range(5):
                year = start_year + i
                item = data_map.get(year, {})
                daily_stats.append({
                    'label': str(year),
                    'registered': item.get('registered', 0),
                    'guest': item.get('guest', 0),
                })

        else:
            return Response({'error': 'Invalid filter type'}, status=400)

        return Response(daily_stats)
    
    @action(detail=False, methods=['get'], url_path='scan-summary/chart', name='scan-summary-chart')
    def customer_scan_summary_chart(self, request):
        filter_type = request.GET.get('filter', 'daily')
        if filter_type == "":
            filter_type = 'daily'
        today = datetime.today().date()

        base_queryset = CustomerHistory.objects.filter(
            updated_at__isnull=False,
        )

        # ---------------- DAILY ----------------
        if filter_type == 'daily':
            start_date = today - timedelta(days=6)
            queryset = (
                base_queryset.filter(updated_at__date__gte=start_date)
                .annotate(day=TruncDate('updated_at'))
                .values('day')
                .annotate(count=Count('id', distinct=True))
                .order_by('day')
            )

            date_count_map = {entry['day']: entry['count'] for entry in queryset}
            result = []
            for i in range(7):
                date = start_date + timedelta(days=i)
                result.append({
                    'label': date.strftime('%Y-%m-%d'),
                    'count': date_count_map.get(date, 0)
                })
            return Response(result)

        # ---------------- WEEKLY ----------------
        elif filter_type == 'week':
            start_date = today - timedelta(weeks=6)
            queryset = (
                base_queryset.filter(updated_at__date__gte=start_date)
                .annotate(week=TruncWeek('updated_at'))
                .values('week')
                .annotate(count=Count('id', distinct=True))
                .order_by('week')
            )

            result = []
            for entry in queryset:
                start = entry['week']
                end = start + timedelta(days=6)
                result.append({
                    'label': f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}",
                    'count': entry['count']
                })
            return Response(result)

        # ---------------- MONTHLY ----------------
        elif filter_type == 'month':
            start_of_year = datetime(today.year, 1, 1).date()
            queryset = (
                base_queryset.filter(updated_at__date__gte=start_of_year)
                .annotate(month=TruncMonth('updated_at'))
                .values('month')
                .annotate(count=Count('id', distinct=True))
                .order_by('month')
            )

            result = [
                {'label': entry['month'].strftime('%B %Y'), 'count': entry['count']}
                for entry in queryset
            ]
            return Response(result)

        # ---------------- YEARLY ----------------
        elif filter_type == 'year':
            start_year = today.year - 6
            years = list(range(start_year, today.year + 1))
            start_date = datetime(start_year, 1, 1).date()
            queryset = (
                base_queryset.filter(updated_at__date__gte=start_date)
                .annotate(year=TruncYear('updated_at'))
                .values('year')
                .annotate(count=Count('id', distinct=True))
                .order_by('year')
            )

            year_count_map = {entry['year'].year: entry['count'] for entry in queryset}
            result = []
            for y in years:
                result.append({
                    'label': y,
                    'count': year_count_map.get(y, 0)
                })
            return Response(result)

        return Response({'error': 'Invalid filter'}, status=400)

    
    @action(detail=False, methods=['get'], url_path='leaderboard/table', name='leaderboard-table')
    def leaderboard_summary_chart(self, request):
        filter_type = request.GET.get('filter', 'all').lower()
        if filter_type == "":
            filter_type = 'all'

        now = timezone.now()

        if filter_type == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == 'all':
            start_date = None
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        point_qs = Point.objects.filter(customer_id__isnull=False)
        if start_date:
            point_qs = point_qs.filter(created_at__gte=start_date)

        point_history_qs = (
            point_qs
            .values('customer_id', 'customer__name', 'customer__email')
            .annotate(
                total_points=Sum('points'),
                product_scan_points=Sum('points', filter=Q(point_type='product_scan')),
                product_review_points=Sum('points', filter=Q(point_type='product_review')),
                product_upload_points=Sum('points', filter=Q(point_type='product_upload')),
                app_referral_points=Sum('points', filter=Q(point_type='app_referral')),
            )
            .order_by('-total_points')[:15]
        )

        result = []
        for rank, record in enumerate(point_history_qs, start=1):
            result.append({
                'customer_name': record['customer__name'],
                'product_scan_points': record['product_scan_points'] or 0,
                'product_review_points': record['product_review_points'] or 0,
                'product_upload_points': record['product_upload_points'] or 0,
                'app_referral_points': record['app_referral_points'] or 0,
                'total_points': record['total_points'] or 0,
            })

        return Response({
            "filter_type": filter_type,
            "total_records": len(result),
            "data": result
        })
