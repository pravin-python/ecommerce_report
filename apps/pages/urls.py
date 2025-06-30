from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.pages.apis.customer_api import CustomerViewSet
from apps.pages.apis.product_api import ProductViewSet
from apps.pages.apis.page_api import PagesViewSet
from django.contrib.auth import views as auth_views
from apps.pages import views

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'pages', PagesViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('submit-dashboard-component/', views.dashboard_component_submit, name='submit-dashboard-component'),
    path('update-dashboard-component/position', views.update_component_order, name='update-dashboard-component-position'),
    path('user-profile/', views.user_profile, name = 'user_profile'),
    path('accounts/auth-signup/', views.auth_signup, name = 'auth_signup'),
    path('accounts/auth-signin/', views.AuthSignin.as_view(), name='auth_signin'),
    path('accounts/forgot-password/', views.UserPasswordResetView.as_view(), name='forgot_password'),
    path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',  views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('accounts/logout/', views.user_logout_view, name='logout'),
    path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name="password_change_done" ),

    # registred api
    path('api/', include(router.urls)),

]