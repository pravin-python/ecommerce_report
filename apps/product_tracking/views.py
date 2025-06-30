import os
import pickle

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account
from google.analytics.data_v1beta.types import (
        Dimension,
        Metric,
        DateRange,
        RunReportRequest,
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db.models import Count, Q
from apps.product_tracking.models import Category, Product, Metafield
from apps.customer_info.models import CustomerHistory, Customer
from apps.product_tracking.models import Product
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
def scanned_categories(request):
    search_query = request.GET.get('search', '').strip()
    order = request.GET.get('order', '').strip()
    scan_count_filter = request.GET.get('scan_count', '').strip()
    per_page = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    if order == 'asc':
        sort = False
    else:
        sort = True

    try:
        scan_count = int(scan_count_filter)
    except (ValueError, TypeError):
        scan_count = 0  # Default: show all

    parent_categories = Category.objects.filter(parent_id__isnull=True)
    if search_query:
        parent_categories = parent_categories.filter(name__icontains=search_query)
    parent_categories = parent_categories.annotate(
        scan_count=Count('products__customerhistory')
    )

    if scan_count > 0:
        parent_categories = parent_categories.filter(scan_count__gte=scan_count)

    categories_data = []
    for parent in parent_categories:
        children = Category.objects.filter(parent_id=parent.id)
        if search_query:
            children = children.filter(name__icontains=search_query)
        children = children.annotate(
            scan_count=Count('products__customerhistory')
        )
        categories_data.append({
            'parent': parent,
            'children': children
        })

    sorted_categories = sorted(categories_data, key=lambda p: p['parent'].scan_count, reverse=sort)

    paginator = Paginator(sorted_categories, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    copy_querydict = query_params.copy()
    copy_querydict.pop('order', None)
    query_sort_oder = copy_querydict.urlencode()
    current_params = query_params.urlencode()

    context = {
        "title": "Most Scanned Categories",
        "breadcrumb_items": [
            {"label": "Categories", "url": None},
        ],
        'page_obj': page_obj,
        'search_query': search_query,
        'scan_count_filter': scan_count_filter,
        'current_params': current_params,
        "query_sort_oder": query_sort_oder
    }

    return render(request, 'product_tracking/scanned-categories.html', context)

    
def child_category_detail(request, parent_id):
    search_query = request.GET.get('search', '').strip()
    parent = get_object_or_404(Category, id=parent_id)
    per_page = request.GET.get('per_page', '10').strip()
    scan_count_filter = request.GET.get('scan_count', '').strip()
    order = request.GET.get('order', '').strip()

    try:
        per_page = int(per_page) if per_page.isdigit() else 10
    except:
        per_page = 10

    try:
        scan_count = int(scan_count_filter)
    except (ValueError, TypeError):
        scan_count = 0

    if order == 'asc':
        sort_reverse = False
    else:
        sort_reverse = True

    children = (
        Category.objects
        .filter(parent_id=parent.id)
        .annotate(scan_count=Count('products__customerhistory'))
    )
    if search_query:
        children = children.filter(name__icontains=search_query)
    if scan_count > 0:
        children = children.filter(scan_count__gte=scan_count)

    # Sort by scan_count
    children = sorted(children, key=lambda c: c.scan_count, reverse=sort_reverse)

    paginator = Paginator(children, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    copy_querydict = query_params.copy()
    copy_querydict.pop('order', None)
    query_sort_oder = copy_querydict.urlencode()

    context =  {
         "title": "Scanned Categories",
        "breadcrumb_items": [
            {"label": "Most Scanned Categories", "url": 'most_scanned_categories'},
            {"label": parent.name, "url": None},
        ],
        'page_obj': page_obj,
        'query_sort_oder': query_sort_oder,
        'order': order,
    }

    return render(request, 'product_tracking/child-category-detail.html', context)
    
def products(request):
    product_list = Product.objects.order_by('-id')

    # Filters from GET params
    per_page = request.GET.get('per_page', '25').strip()
    diet_filter = request.GET.getlist('diet[]')
    status_filter = request.GET.getlist('status[]')
    grade_filter = request.GET.getlist('grade[]')
    score_range = request.GET.get('scoreRange', '')
    food_category_filter = request.GET.getlist('food_category[]')
    category_filter = request.GET.getlist('category[]')
    search_query = request.GET.get('search')
    
    try:
        per_page = int(per_page) if per_page.isdigit() else 25
    except:
        per_page = 25

    # Apply filters
    if search_query:
        product_list = product_list.filter(Q(name__icontains=search_query))

    if diet_filter:
        product_list = product_list.filter(diet__in=diet_filter)

    if status_filter:
        product_list = product_list.filter(status__in=status_filter)

    if grade_filter:
        product_list = product_list.filter(grade_in__in=grade_filter)

    if food_category_filter:
        product_list = product_list.filter(food_category__in=food_category_filter)

    score_min = 1
    score_max = 100
    if score_range:
        score_min, score_max = map(int, score_range.split(","))
        if (score_min > 1 and score_max == 100) or (score_min == 1 and score_max < 100) or (score_min > 1 and score_max < 100):
            try:
                product_list = product_list.filter(
                    score_in__gte=score_min,
                    score_in__lte=score_max
                )
            except:
                pass
    
    if category_filter:
        all_category_ids = list(category_filter)
        child_ids = Category.objects.filter(parent_id__in=category_filter).values_list('id', flat=True)
        all_category_ids.extend(child_ids)
        product_list = product_list.filter(category__id__in=all_category_ids)

    paginator = Paginator(product_list, per_page)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    parent_categories = Category.objects.filter(parent_id__isnull=True)
    category_choices = [(cat.id, cat.name) for cat in parent_categories]

    context = {
        "title": "All Products",
        "breadcrumb_items": [
            {"label": "All Products", "url": None},
        ],
        'page_obj': page_obj,
        'diet_choices': Product.DIET_CHOICES,
        'status_choices': Product.STATUS_CHOICES,
        'grade_choices': Product.GRADE_CHOICES,
        'food_category_choices': Product.FOOD_CATEGORY_CHOICES,
        'category_choices': category_choices,
        'selected_diet': diet_filter,
        'selected_statuses': status_filter,
        'selected_grades': grade_filter,
        'selected_food_categories': food_category_filter,
        'selected_categories': category_filter,
        'score_min': score_min,
        'score_max': score_max,
    }

    return render(request, 'product_tracking/product.html', context)

@login_required(login_url='/accounts/auth-signin/')
def most_scanned_products(request):
    querydict = request.GET.copy()

    search_query = request.GET.get('count', '').strip()
    search = request.GET.get('search', '').strip()
    order = request.GET.get('order', '').strip()
    score_range = request.GET.get('scoreRange', '').strip()
    status_filter = request.GET.getlist('status[]')
    grade_filter = request.GET.getlist('grade[]')

    if order == 'asc':
        sort = False
    else:
        sort = True

    try:
        scan_count = int(search_query)
    except (ValueError, TypeError):
        scan_count = 10 

    scanned_data = (
        CustomerHistory.objects
        .values('product_id')
        .annotate(scan_count=Count('id'))
        .filter(scan_count__gte=scan_count)
        .order_by('-scan_count')
    )

    if search:
        scanned_data = scanned_data.filter(
            Q(product__barcode__icontains=search) |
            Q(product__name__icontains=search)
        )
    
    if status_filter:
        scanned_data = scanned_data.filter(product__status__in=status_filter)

    if grade_filter:
        scanned_data = scanned_data.filter(product__grade_in__in=grade_filter)

    score_min = 1
    score_max = 100
    try:
        if score_range:
            score_min, score_max = map(int, score_range.split(","))
            if (score_min > 1 and score_max == 100) or (score_min == 1 and score_max < 100) or (score_min > 1 and score_max < 100):
                scanned_data = scanned_data.filter(
                    product__score_in__gte=score_min,
                    product__score_in__lte=score_max
                )
    except:
        pass
    product_ids = [item['product_id'] for item in scanned_data]
    products = Product.objects.filter(id__in=product_ids)

    scan_count_map = {item['product_id']: item['scan_count'] for item in scanned_data}

    for product in products:
        product.scan_count = scan_count_map.get(product.id, 0)

    sorted_products = sorted(products, key=lambda p: p.scan_count, reverse=sort)

    copy_querydict = querydict.copy()
    copy_querydict.pop('sort_by', None)
    copy_querydict.pop('order', None)
    query_sort_oder = copy_querydict.urlencode()

    paginator = Paginator(sorted_products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Most Scanned Products",
        "breadcrumb_items": [
            {"label": "Most Scanned Products", "url": None},
        ],
        'page_obj': page_obj,
        'scan_count' : scan_count,
        'selected_statuses': status_filter,
        'selected_grades': grade_filter,
        'query_sort_oder': query_sort_oder,
        'status_choices': Product.STATUS_CHOICES,
        'grade_choices': Product.GRADE_CHOICES,
        'score_min' : score_min,
        'score_max' : score_max,
    }

    context.update(header_component(
        table={
            "name": "most_top_10_scan_products_table",
            "ajax_url": "/api/products/most-scan/table"
        }
    ))

    return render(request, 'product_tracking/most_scanned_products.html', context)

def product_not_found(request):
    per_page = request.GET.get('per_page', 10)
    search_query = request.GET.get('search', '').strip()
    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = 10

    entries = Metafield.objects.filter(type='Product_not_found').order_by('-created_at')

    customer_ids = entries.values_list('customer_id', flat=True).distinct()
    customers = Customer.objects.filter(id__in=customer_ids)

    if search_query:
        customers = customers.filter(name__icontains=search_query)

    customer_map = {c.id: c for c in customers}

    customer_latest_entries = {}
    for entry in entries:
        if entry.customer_id in customer_map:
            if entry.customer_id not in customer_latest_entries:
                customer_latest_entries[entry.customer_id] = entry
            elif entry.created_at > customer_latest_entries[entry.customer_id].created_at:
                customer_latest_entries[entry.customer_id] = entry

    data = []
    for customer_id, entry in customer_latest_entries.items():
        customer = customer_map.get(customer_id)
        data.append({
            'customer_name': customer.name if customer else 'Unknown',
            'customer_id': customer_id,
            'latest_date': entry.created_at
        })

    data.sort(key=lambda x: x['latest_date'], reverse=True)

    paginator = Paginator(data, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    context = {
        "title": "Product Not Found",
        "breadcrumb_items": [
            {"label": "Unrecognized Products by Customer", "url": None},
        ],
        'page_obj': page_obj,
        'search_query': search_query,
        'current_params': current_params
    }

    return render(request, "product_tracking/product-not-found.html", context)


def product_not_found_by_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    entries = (
        Metafield.objects
        .filter(customer_id=customer_id, type='Product_not_found')
        .order_by('-created_at')
    )

    value_map = {}
    for entry in entries:
        if entry.value not in value_map:
            value_map[entry.value] = {
                'count': 1,
                'latest_entry': entry
            }
        else:
            value_map[entry.value]['count'] += 1
            if entry.created_at > value_map[entry.value]['latest_entry'].created_at:
                value_map[entry.value]['latest_entry'] = entry

    data = []
    for value, info in value_map.items():
        data.append({
            'value': value,
            'count': info['count'],
            'created_at': info['latest_entry'].created_at
        })

    order = request.GET.get('order', '').strip()
    if order == 'asc':
        sort_reverse = False
    else:
        sort_reverse = True

    data.sort(key=lambda x: (x['count'], x['created_at']), reverse=sort_reverse)

    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(data, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    current_params = query_params.urlencode()

    copy_querydict = request.GET.copy()
    copy_querydict.pop('order', None)
    query_sort_oder = copy_querydict.urlencode()

    return render(request, "product_tracking/product-not-found-detail.html", {
        'customer': customer,
        'page_obj': page_obj,
        'current_params': current_params,
        'query_sort_oder': query_sort_oder,
    })

@csrf_exempt
def most_viewed_products(request):
    # Google Analytics setup
    KEY_PATH = "apps/product_tracking/ecommerce.json"
    PROPERTY_ID = "124567890"
    CACHE_FILE = "apps/product_tracking/most_viewed_products_cache.pkl"

    refresh = request.GET.get('refresh', '').lower() == 'true'
    data_loaded_from_cache = False

    # Try to load cached data unless refresh requested
    if not refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                cached = pickle.load(f)
                product_views = cached.get("product_views", [])
                total_products_id = cached.get("total_products_id", 0)
                data_loaded_from_cache = True
        except Exception:
            product_views = []
            total_products_id = 0
    else:
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        client = BetaAnalyticsDataClient(credentials=credentials)
        try:
            request_ga = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                dimensions=[
                    Dimension(name="eventName"),
                    Dimension(name="customEvent:productId"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                ],
                date_ranges=[
                    DateRange(start_date="today", end_date="today")
                ],
            )
            response = client.run_report(request_ga)
            print("Google Analytics response:", response)
        except Exception as e:
            return render(request, "product_tracking/most_viewed_products.html", {
                "error": f"Google Analytics error: {e}"
            })

        product_views = []
        for row in response.rows:
            event_name = row.dimension_values[0].value
            if event_name == "product_detail":
                product_id = row.dimension_values[1].value
                event_count = int(row.metric_values[0].value)
                if product_id and product_id.isdigit():
                    product_views.append((int(product_id), event_count))
        total_products_id = len(product_views)
        # Save to cache
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump({
                    "product_views": product_views,
                    "total_products_id": total_products_id
                }, f)
        except Exception:
            pass

    product_views.sort(key=lambda x: x[1], reverse=True)
    product_ids = [pid for pid, _ in product_views]
    products = Product.objects.filter(id__in=product_ids)
    product_map = {p.id: p for p in products}

    data = []
    for pid, count in product_views:
        product = product_map.get(pid)
        if product:
            data.append({
                "id": product.id,
                "name": product.name,
                "barcode": product.barcode,
                "score": getattr(product, "score_in", None),
                "grade": getattr(product, "grade_in", None),
                "status": getattr(product, "status", None),
                "views": count,
                "not_found": False,
                "event_count": count,
            })
        # # # Uncomment this block if you want to show products not found in the database
        # else:
        #     data.append({
        #         "id": pid,
        #         "name": "Not found in database",
        #         "score": None,
        #         "grade": None,
        #         "status": None,
        #         "views": count,
        #         "not_found": True,
        #         "event_count": count,
        #     })

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.getlist('status[]')
    grade_filter = request.GET.getlist('grade[]')
    score_range = request.GET.get('scoreRange', '')

    if search_query:
        data = [item for item in data if not item["not_found"] and search_query.lower() in item["name"].lower()]
    if status_filter:
        data = [item for item in data if not item["not_found"] and item["status"] in status_filter]
    if grade_filter:
        data = [item for item in data if not item["not_found"] and item["grade"] in grade_filter]

    score_min = 1
    score_max = 100
    if score_range:
        try:
            score_min, score_max = map(int, score_range.split(","))
            if (score_min > 1 and score_max == 100) or (score_min == 1 and score_max < 100) or (score_min > 1 and score_max < 100):
                data = [item for item in data if not item["not_found"] and item["score"] is not None and score_min <= item["score"] <= score_max]
        except (ValueError, TypeError):
            pass

    per_page = request.GET.get('per_page', 15)
    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = 15

    paginator = Paginator(data, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    if 'refresh' in query_params:
        query_params.pop('refresh')
    current_params = query_params.urlencode()

    return render(request, "product_tracking/most_viewed_products.html", {
        "page_obj": page_obj,
        "current_params": current_params,
        "total_products_id": total_products_id,
        "event_count": [count for _, count in product_views],
        "search_query": search_query,
        'status_choices': Product.STATUS_CHOICES,
        'grade_choices': Product.GRADE_CHOICES,
        'selected_statuses': status_filter,
        'selected_grades': grade_filter,
        'score_min': score_min,
        'score_max': score_max,
        'data_loaded_from_cache': data_loaded_from_cache,
        'refresh_url': request.path + ('?' + current_params if current_params else '') + ('&' if current_params else '?') + 'refresh=true',
    })