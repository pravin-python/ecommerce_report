import json
from calendar import monthrange
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict  

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear

from apps.customer_info.models import *
from apps.product_tracking.models import Product, Metafield
from apps.pages.models import DashboardComponent

def header_component(table: dict = None, chart: dict = None):
    return_data = {
        "show_chart": False,
        "show_table": False,
        "chart": None,
        "table": None,
        "chart_component": {},
        "table_component": {}
    }

    # Chart Component
    if chart:
        chart_instance = DashboardComponent.objects.filter(name=chart.get("name")).first()
        return_data["show_chart"] = True
        return_data["chart"] = chart_instance

        return_data["chart_component"] = {
            "is_chart": True,
            "name": chart.get("name"),
            "ajax_url": chart.get("ajax_url"),
            "chart_type": chart.get("chart_type") or getattr(chart_instance, "chart_type", "area"),
            "is_filter": chart.get("is_filter", False),
            "filter_buttons": chart.get("filter_buttons", {}),
        }

    # Table Component
    if table:
        table_instance = DashboardComponent.objects.filter(name=table.get("name")).first()
        return_data["show_table"] = True
        return_data["table"] = table_instance

        return_data["table_component"] = {
            "is_table": True,
            "name": table.get("name"),
            "ajax_url": table.get("ajax_url"),
            "is_filter": table.get("is_filter", False),
            "filter_buttons": table.get("filter_buttons", {}),
        }

    return return_data

@login_required(login_url='/accounts/auth-signin/')
def scan_history(request):
    search_query = request.GET.get('search', '').strip()
    per_page = request.GET.get('per_page', '10').strip()
    status_filter = request.GET.getlist('status[]')
    grade_filter = request.GET.getlist('grade[]')
    updated_at_start = request.GET.get('date_start', '').strip()
    updated_at_end = request.GET.get('date_end', '').strip()
    score_range = request.GET.get('scoreRange', '').strip()

    customer_history_qs = CustomerHistory.objects.select_related('customer', 'product').order_by('-updated_at')

    if search_query:
        customer_history_qs = customer_history_qs.filter(
            Q(product__name__icontains=search_query) |
            Q(product__barcode__icontains=search_query) |
            Q(customer__name__icontains=search_query)
        )

    if status_filter:
        customer_history_qs = customer_history_qs.filter(product__status__in=status_filter)

    if grade_filter:
        customer_history_qs = customer_history_qs.filter(product__grade_in__in=grade_filter)

    if updated_at_start:
        try:
            start_date = parse_date(updated_at_start)
            if start_date:
                customer_history_qs = customer_history_qs.filter(updated_at__date__gte=start_date)
        except:
            pass

    if updated_at_end:
        try:
            end_date = parse_date(updated_at_end)
            if end_date:
                customer_history_qs = customer_history_qs.filter(updated_at__date__lte=end_date)
        except:
            pass

    score_min = 1
    score_max = 100
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
        if score_range:
            score_min, score_max = map(int, score_range.split(","))
            if (score_min > 1 and score_max == 100) or (score_min == 1 and score_max < 100) or (score_min > 1 and score_max < 100):
                customer_history_qs = customer_history_qs.filter(
                    product__score_in__gte=score_min,
                    product__score_in__lte=score_max
                )
    except:
        pass

    paginator = Paginator(customer_history_qs, per_page)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context = {
        "title": "Customer Scanned Products",
        "breadcrumb_items": [
            {"label": "Customer Scanned Products", "url": None},
        ],
        'page_obj': page_obj,
        'status_choices': Product.STATUS_CHOICES,
        'grade_choices': Product.GRADE_CHOICES,
        'selected_statuses': status_filter,
        'selected_grades': grade_filter,
        'score_min' : score_min,
        'score_max' : score_max,
    }

    context.update(header_component(
        chart={
            "name": "customer_scanned_products_chart",
            "ajax_url": "/api/customers/scan-summary/chart",
            "chart_type": "area",
            "is_filter": True,
            "filter_buttons": {
                "daily": "Daily",
                "week": "Weekly",
                "month": "Monthly",
                "year": "Yearly"
            }
        },
        table={
            "name": "customer_scanned_products_table",
            "ajax_url": "/api/customers/scan-summary/table"
        }
    ))

    return render(request, 'customers_info/customer_scan_history.html', context)

@login_required(login_url='/accounts/auth-signin/')
def customer_points(request):
    querydict = request.GET.copy()

    search = querydict.get('search', '').strip()
    per_page = request.GET.get('per_page', '10').strip()
    sort_by = querydict.get('sort_by', 'total_points')
    order = querydict.get('order', 'desc')
    sort_time = querydict.get('sort_time')

    today = datetime.today().date()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    # Date range filter based on sort_time
    if sort_time == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif sort_time == 'this_month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=monthrange(today.year, today.month)[1])
    elif sort_time == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = end_date = None

    allowed_sort_fields = {
        'product_upload_points', 'product_review_points', 'product_share_points',
        'product_scan_points', 'app_referral_points', 'referred_by_points',
        'customer__name', 'total_points'
    }

    if sort_by not in allowed_sort_fields:
        sort_by = 'total_points'
    ordering = f'-{sort_by}' if order == 'desc' else sort_by

    # Base queryset with filter
    point_qs = Point.objects.filter(customer_id__isnull=False)

    if start_date and end_date:
        point_qs = point_qs.filter(created_at__range=(start_date, end_date))

    if search:
        point_qs = point_qs.filter(customer__name__icontains=search)

    point_history_qs = (
        point_qs
        .values('customer_id', 'customer__name', 'customer__email')
        .annotate(
            total_points=Sum('points'),
            product_scan_points=Sum('points', filter=Q(point_type='product_scan')),
            product_review_points=Sum('points', filter=Q(point_type='product_review')),
            product_upload_points=Sum('points', filter=Q(point_type='product_upload')),
            product_share_points=Sum('points', filter=Q(point_type='product_share')),
            profile_completion_points=Sum('points', filter=Q(point_type='profile_completion')),
            app_referral_points=Sum('points', filter=Q(point_type='app_referral')),
            referred_by_points=Sum('points', filter=Q(point_type='referred_by')),
        )
        .order_by(ordering)
    )

    # Efficient pagination
    paginator = Paginator(point_history_qs, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Clean querystrings
    query_time = querydict.copy()
    query_time.pop('sort_time', None)
    query_time = query_time.urlencode()

    # Compute percent fields efficiently
    for record in page_obj.object_list:
        total = record['total_points'] or 1
        record['product_upload_percent'] = round((record.get('product_upload_points') or 0) * 100 / total, 2)
        record['product_review_percent'] = round((record.get('product_review_points') or 0) * 100 / total, 2)
        record['product_scan_percent'] = round((record.get('product_scan_points') or 0) * 100 / total, 2)
        record['app_referral_percent'] = round((record.get('app_referral_points') or 0) * 100 / total, 2)
        record['other_points_percent'] = round(100 - (
            record['product_upload_percent'] +
            record['product_review_percent'] +
            record['product_scan_percent'] +
            record['app_referral_percent']
        ), 2)

    context = {
        "title": "Leaderboard",
        "breadcrumb_items": [
            {"label": "Leaderboard", "url": None},
        ],
        "show_table": True,
        'page_obj': page_obj,
        'point_types': Point.POINT_TYPE_CHOICES,
        'query_time': query_time,
        'table_headers': [
            ('customer__name', 'Customer Name'),
            ('product_upload_points', 'Add Product'),
            ('product_review_points', 'Product Review'),
            ('product_scan_points', 'Product Scan'),
            ('app_referral_points', 'App Refer'),
            ('total_points', 'Total Point'),
        ]
    }

    context.update(header_component(
        table={
            "name": "leaderboard_summary_table",
            "ajax_url": "/api/customers/leaderboard/table",
            "is_filter": True,
            "filter_buttons": {
                "all": "All Time",
                "week": "Weekly",
                "month": "Monthly",
            }
        },
    ))
    return render(request, 'customers_info/customer_points.html', context)

@login_required(login_url='/accounts/auth-signin/')
def get_customer(request):
    
    per_page = request.GET.get('per_page', '10').strip()
    search_query = request.GET.get('search')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    is_guest_filter = request.GET.get('is_guest')
    diet_filter = request.GET.get('by_diet')

    customers = Customer.objects.all().order_by('-id')
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query)
        )
        
    if from_date and to_date:
        try:
            customers = customers.filter(created_at__date__gte=from_date, created_at__date__lte=to_date)
            print(customers)
        except ValueError:
            pass
    
    if is_guest_filter:
        if is_guest_filter == 'true':
            customers = customers.filter(is_guest=True)
        elif is_guest_filter == 'false':
            customers = customers.filter(is_guest=False)

    if diet_filter:
        customers = customers.filter(diet=diet_filter)

    diet_choices = [
        (code, label)
        for code, label in Customer._meta.get_field('diet').choices
        if Customer.objects.filter(diet=code).exists()
    ]
    
    registered_users = customers.filter(is_guest=False).count()
    guest_users = customers.filter(is_guest=True).count()
    total_users = customers.count()
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('referral_page', None)
    params_string = query_params.urlencode()
    current_params = params_string

    paginator = Paginator(customers.order_by('-id'), per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    current_params = query_params.urlencode()

    context={
        "title": "Customers",
        "breadcrumb_items": [
            {"label": "Customers", "url": None},
        ],
        'registered_users': registered_users,
        'guest_users': guest_users,
        'total_users': total_users,
        'page_obj': page_obj,
        'from_date': from_date,
        'to_date': to_date,
        'current_params': current_params,
        'is_guest_filter': is_guest_filter,
        'diet_filter': diet_filter,
        'diet_choices': diet_choices,
        'params_string': params_string,
    }

    context.update(header_component(
        chart={
            "name": "customers_chart",
            "ajax_url": "/api/customers/chart",
            "chart_type": "bar",
            "is_filter": True,
            "filter_buttons": {
                "daily": "Daily",
                "week": "Weekly",
                "month": "Monthly",
                "year": "Yearly"
            }
        },
        table={
            "name": "customers_table",
            "ajax_url": "/api/customers/table",
            "is_filter": True,
            "filter_buttons": {
                "registered": "Registered Customers",
                "guest": "Guest Customers",
            }
        }
    ))
    
    return render(request, 'customers_info/customer.html', context)


def referred_by_customer(request):
    search_referred_user = request.GET.get('search_referred_user')
    referrals = (
        Customer.objects
        .values('referred_by')
        .annotate(total_referrals=Count('id'))
        .exclude(referred_by__isnull=True)
        .order_by('-total_referrals')
    )
    
    referred_ids = [item['referred_by'] for item in referrals if item['referred_by']]
    referrers = Customer.objects.filter(id__in=referred_ids).in_bulk()

    for item in referrals:
        referrer_id = item['referred_by']
        item['referrer_name'] = referrers.get(referrer_id).name if referrer_id in referrers else 'None'
        
    if search_referred_user:
        referrals = [
            item for item in referrals
            if search_referred_user.lower() in (referrers.get(item['referred_by']).name.lower() if item['referred_by'] in referrers and referrers.get(item['referred_by']).name else '')
        ]

    referral_page_number = request.GET.get('page')
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    referral_paginator = Paginator(referrals, per_page)
    referral_page_obj = referral_paginator.get_page(referral_page_number)

    total_referred_users = Customer.objects.filter(referred_by__isnull=False).count()
    total_non_referred_users = Customer.objects.filter(referred_by__isnull=True).count()
    
    query_params = request.GET.copy()
    if 'referral_page' in query_params:
        query_params.pop('referral_page')
    current_params = query_params.urlencode()
    context = {
        "title": "Referred By Customer",
        "breadcrumb_items": [
            {"label": "Customers", "url": None},
        ],
        'page_obj': referral_page_obj,
        'total_referred_users': total_referred_users,
        'total_non_referred_users': total_non_referred_users,
        'current_params': current_params
    }
    return render(request, 'customers_info/referred_by_users.html', context)

def customer_referred_list(request, referrer_id):
    referrer = get_object_or_404(Customer, id=referrer_id)

    search_query = request.GET.get('search')
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    referred_users_qs = Customer.objects.filter(referred_by=referrer_id).order_by('-id')

    if search_query:
        referred_users_qs = referred_users_qs.filter(
            Q(name__icontains=search_query) | Q(email__icontains=search_query)
        )

    paginator = Paginator(referred_users_qs, per_page)
    page_number = request.GET.get('page')
    referred_users = paginator.get_page(page_number)
    
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    context = {
        "title": f"Customer referred by {referrer.name }",
        "breadcrumb_items": [
            {"label": "Referred By Customer", "url": 'referred_by_customer'},
            {"label": referrer.name , "url": None},
        ],
        'referrer': referrer,
        'page_obj': referred_users,
        "current_params": current_params,
    }

    return render(request, 'customers_info/customer_referred_list.html', context)


def customer_product_reviews(request):
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.getlist('status')
    score_range = request.GET.get('scoreRange', '').strip()
    per_page = request.GET.get('per_page', '10').strip()

    reviews = ProductReview.objects.select_related('customer', 'product').order_by('-created_at')

    if search_query:
        reviews = reviews.filter(
            Q(customer__name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(review__icontains=search_query) |
            Q(update_request__icontains=search_query)
        )

    if status_filter:
        reviews = reviews.filter(status__in=status_filter)
        
    score_min = 1
    score_max = 5
    try:
        if score_range:
            score_min, score_max = map(float, score_range.split(","))
            if (score_min > 1 and score_max == 5) or (score_min == 1 and score_max < 5) or (score_min > 1 and score_max < 5):
                reviews = reviews.filter(
                    rating__gte=score_min,
                    rating__lte=score_max
                )
    except:
        pass    

    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    paginator = Paginator(reviews, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    table_data = []
    for review in page_obj.object_list:
        if review.status == 'processing':
            try:
                update_data = json.loads(review.update_request or '{}')
                review_value = update_data.get('review', '')
            except Exception:
                review_value = ''
        else:
            review_value = review.review
        table_data.append({
            'customer_name': review.customer.name if review.customer else '',
            'product_name': review.product.name if review.product else '',
            'review': review_value,
            'rating': int(review.rating) if review.rating is not None else None,
            'date': review.created_at,
            'status': dict(ProductReview.STATUS_CHOICES).get(review.status, review.status),
        })

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    context = {
        "title": "Customer Product Reviews",
        "breadcrumb_items": [
            {"label": "Product Reviews by Customer", "url": None},
        ],
        'table_data': table_data,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_choices': ProductReview.STATUS_CHOICES,
        'selected_statuses': status_filter,
        'current_params': current_params,
        'score_min' : score_min,
        'score_max' : score_max,
    }

    return render(request, "customers_info/customer_product_review.html", context)

def product_problem_report(request):
    reports = (
        Metafield.objects
        .filter(type='Report')
        .select_related('product')
        .order_by('-created_at')
    )
    search_query = request.GET.get('search', '').strip()
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    if search_query:
        customer_ids = list(
            Customer.objects.filter(name__icontains=search_query).values_list('id', flat=True)
        )
        reports = reports.filter(
            Q(product__name__icontains=search_query) |
            Q(value__icontains=search_query) |
            Q(customer_id__in=customer_ids)
        )

    paginator = Paginator(reports, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    customer_ids = set(report.customer_id for report in page_obj.object_list)
    customers = Customer.objects.filter(id__in=customer_ids)
    customer_map = {c.id: c for c in customers}

    report_data = []
    for report in page_obj.object_list:
        customer = customer_map.get(report.customer_id)
        product = report.product
        report_data.append({
            'id': report.id,
            'customer_name': customer.name if customer else 'Unknown',
            'product_name': product.name if product else 'Unknown',
            'type': dict(Metafield.TYPE_CHOICES).get(report.type, report.type),
            'value': report.value,
            'created_at': report.created_at,
        })

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    return render(request, "customers_info/customer_product_problem_report.html", {
        "title": "Customer Product Problem Report",
        "breadcrumb_items": [
            {"label": "Product Problem Report", "url": None},
        ],
        'report_data': report_data,
        'page_obj': page_obj,
        'current_params': current_params,
    })

def customer_allergies_lists(request):
    allergies = Metafield.objects.filter(type='Allergy').order_by('-created_at')
    search_query = request.GET.get('search', '').strip()

    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    if search_query:
        # First, get customer IDs matching the search query
        customer_ids = list(
            Customer.objects.filter(name__icontains=search_query).values_list('id', flat=True)
        )
        allergies = allergies.filter(
            Q(customer_id__in=customer_ids)
        )
    paginator = Paginator(allergies, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    customer_ids = set(obj.customer_id for obj in page_obj.object_list)
    customers = Customer.objects.filter(id__in=customer_ids)
    customer_map = {c.id: c for c in customers}

    allergies_data = []
    for allergy in page_obj.object_list:
        allergy_list = []
        try:
            allergy_list = json.loads(allergy.value)
            allergy_list = [a for a in allergy_list if a.strip()]
        except Exception:
           pass

        customer = customer_map.get(allergy.customer_id)
        allergies_data.append({
            'customer_name': customer.name if customer else 'None',
            'allergy_type': allergy.type,
            'allergy_value': ', '.join(allergy_list),
            'created_at': allergy.created_at,
        })

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    return render(request, "customers_info/customer_allergies_list.html", {
        'allergies_data': allergies_data,
        'page_obj': page_obj,
        'current_params': current_params,
    })

def customer_uploads_products(request):
    search_query = request.GET.get('search', '').strip()
    per_page = request.GET.get('per_page', '10').strip()

    uploads = CustomerUpload.objects.all().order_by('-created_at')

    if search_query:
        customer_ids_by_name = list(
            Customer.objects.filter(name__icontains=search_query).values_list('id', flat=True)
        )
        uploads = uploads.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(brand_name__icontains=search_query) |
            Q(customer_id__in=customer_ids_by_name)
        )

    customer_ids = uploads.values_list('customer_id', flat=True).distinct()
    customers = Customer.objects.filter(id__in=customer_ids)

    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    paginator = Paginator(customers, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "customers_info/customer_uploads_products.html", {
        "title": "Customers Contributed Products",
        "breadcrumb_items": [
            {"label": "Products uploads via Customer", "url": None},
        ],
        'page_obj': page_obj,
        'search_query': search_query,
    })

def customer_product_details(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    uploads = CustomerUpload.objects.filter(customer_id=customer_id).order_by('-created_at')
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.getlist('status')
    
    if search_query:
        uploads = uploads.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(brand_name__icontains=search_query)
        )

    if status_filter:
        uploads = uploads.filter(status__in=status_filter)

    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    paginator = Paginator(uploads, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    table_data = []
    for upload in page_obj.object_list:
        table_data.append({
            'product_name': upload.name,
            'barcode': upload.barcode,
            'brand_name': upload.brand_name,
            'status': dict(CustomerUpload.STATUS_CHOICES).get(upload.status, upload.status),
            'reason': upload.reason,
            'updated_at': upload.updated_at,
        })

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    return render(request, "customers_info/customer_product_uploads_details.html", {
        'customer': customer,
        'table_data': table_data,
        'page_obj': page_obj,
        'search_query': search_query,
        'current_params': current_params,
        'status_choices': CustomerUpload.STATUS_CHOICES,
        'selected_statuses': status_filter,
    })
    



# this function not use

def customer_list_items(request):
    customer_lists = (
        CustomerList.objects
        .select_related('customer')
        .all()
        .order_by('-id')
    )
    search_query = request.GET.get('search_customer_name')
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10
    grouped_data = defaultdict(list)
    for cl in customer_lists:
        # Only include lists that have at least one product
        if CustomerListItem.objects.filter(customer_list=cl).exists():
            grouped_data[cl.customer].append(cl)

    if search_query:
        filtered_grouped_data = {
            customer: lists
            for customer, lists in grouped_data.items()
            if search_query.lower() in (customer.name or '').lower() or search_query.lower() in (customer.email or '').lower()
        }
    else:
        filtered_grouped_data = grouped_data

    paginator = Paginator(list(filtered_grouped_data.items()), per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    return render(request, 'customers_info/customer_list_items.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'current_params': current_params,
    })
    
def customer_list_detail(request, list_id):
    search_query = request.GET.get('search', '').strip()
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    customer_list = get_object_or_404(CustomerList, id=list_id)
    items = (
        CustomerListItem.objects
        .select_related('product')
        .filter(customer_list=customer_list)
    )

    if search_query:
        items = items.filter(product__name__icontains=search_query)

    paginator = Paginator(items, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    return render(request, 'customers_info/customer_list_detail.html', {
        "title": f"{ customer_list.customer.name } - { customer_list.name }",
        "breadcrumb_items": [
            {"label": "Customer List Items", "url": "customer_list_items"},
        ],
        'customer_list': customer_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'current_params': current_params,
    })