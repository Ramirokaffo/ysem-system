from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('modules/', views.select_module_view, name='select_module'),
    path('roles-info/', views.roles_info_view, name='roles_info'),

    path(
        '2fa/login/challenge/',
        views.two_factor_login_challenge_view,
        name='two_factor_login_challenge',
    ),
    path(
        '2fa/login/confirm/<str:token>/',
        views.two_factor_login_confirm_link_view,
        name='two_factor_login_confirm_link',
    ),
    path(
        '2fa/toggle/init/',
        views.two_factor_toggle_init_view,
        name='two_factor_toggle_init',
    ),
    path(
        '2fa/toggle/verify/',
        views.two_factor_toggle_verify_view,
        name='two_factor_toggle_verify',
    ),
    path(
        '2fa/toggle/confirm/<str:token>/',
        views.two_factor_toggle_confirm_link_view,
        name='two_factor_toggle_confirm_link',
    ),
]
