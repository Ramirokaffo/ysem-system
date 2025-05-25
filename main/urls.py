from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('inscriptions/', views.InscriptionsView.as_view(), name='inscriptions'),
    path('etudiants/', views.EtudiantsView.as_view(), name='etudiants'),
    path('documents/', views.DocumentsView.as_view(), name='documents'),
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
    path('parametres/', views.ParametresView.as_view(), name='parametres'),
]
