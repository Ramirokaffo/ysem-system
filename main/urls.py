from django.urls import path
from . import views
from django.conf import settings 
from django.views.generic.base import RedirectView
from django.urls import re_path
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

app_name = 'main'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('inscriptions/', views.InscriptionsView.as_view(), name='inscriptions'),
    path('etudiants/', views.EtudiantsView.as_view(), name='etudiants'),
    path('documents/', views.DocumentsView.as_view(), name='documents'),
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
    path('parametres/', views.ParametresView.as_view(), name='parametres'),
    re_path(r'^favicon\.ico$', favicon_view),

]
