import json
import time
from datetime import timedelta
from django.http import JsonResponse
from django.utils.timezone import now as timezone_now
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


from django.db.models import Count, Q
from apps.pages.forms import RegistrationForm,LoginForm,UserPasswordResetForm,UserSetPasswordForm,UserPasswordChangeForm
from apps.pages.models import DashboardComponent
from apps.pages.forms import DashboardComponentForm
from apps.customer_info.models import CustomerHistory, Customer
from apps.product_tracking.models import Product
from apps.pages.serializers.context_processors import context_label

@login_required(login_url='accounts/auth-signin/')
def index(request):
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

    context = {
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

    return render(request, 'pages/index.html', context)

@csrf_exempt
@login_required(login_url='accounts/auth-signin/')
def dashboard_component_submit(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))

        name = data.get('name')
        is_chart = data.get('is_chart', False)
        is_table = data.get('is_table', False)


        valid_names = context_label().get("context", {}).keys()
        if name not in valid_names:
            return JsonResponse({'status': 'invalid method', 'message': 'Invalid component name'}, status=405)
        

        instance = DashboardComponent.objects.filter(name=name).first()

        if is_chart:
            message = "Dashboard chart component added successfully!"
        elif is_table:
            message = "Dashboard table component added successfully!"
        else:
            message = "Dashboard component removed successfully!"

        if instance:
            form = DashboardComponentForm(data, instance=instance)
        else:
            form = DashboardComponentForm(data)

        if form.is_valid():
            obj = form.save()
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'message': f"Error {form.errors}"}, status=400)
    
    return JsonResponse({'status': 'invalid method'}, status=405)

@require_POST
@csrf_exempt
@login_required(login_url='accounts/auth-signin/')
def update_component_order(request):
    try:
        data = json.loads(request.body)

        names = [item['name'] for item in data if 'name' in item and 'position' in item]
        components = DashboardComponent.objects.filter(name__in=names)
        component_map = {comp.name: comp for comp in components}

        for item in data:
            name = item.get('name')
            position = item.get('position')
            if name in component_map:
                component_map[name].position = position

        DashboardComponent.objects.bulk_update(component_map.values(), ['position'])

        return JsonResponse({'status': 'success', 'message': "Position change successfully"})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# admin_gradient methods add 


@login_required(login_url='accounts/auth-signin/')
def auth_signup(request):
  if request.method == 'POST':
      form = RegistrationForm(request.POST)
      if form.is_valid():
        form.save()
        return redirect('index')
      else:
        print("Registration failed!")
  else:
    form = RegistrationForm()
  context = {'form': form}
  return render(request, 'accounts/auth-signup.html', context)

class AuthSignin(auth_views.LoginView):
    template_name = 'accounts/auth-signin.html'
    form_class = LoginForm
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class UserPasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/forgot-password.html'
    form_class = UserPasswordResetForm

    # def dispatch(self, request, *args, **kwargs):
    #     if request.user.is_authenticated:
    #         return redirect('index')
    #     return super().dispatch(request, *args, **kwargs)

class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
  template_name = 'accounts/recover-password.html'
  form_class = UserSetPasswordForm

class UserPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy('index')

    login_url = reverse_lazy('auth_signin')

class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
  template_name = 'accounts/recover-password.html'
  form_class = UserSetPasswordForm

def user_logout_view(request):
  logout(request)
  return redirect('/accounts/auth-signin/')

# Pages

@login_required(login_url='/accounts/auth-signin')
def user_profile(request):
    return render(request, 'pages/user-profile.html')
    