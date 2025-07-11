from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.student_login, name='login'),
    path('connexion/', views.student_login, name='login'),
    path('deconnexion/', views.student_logout, name='logout'),
    path('tableau-de-bord/', views.student_dashboard, name='dashboard'),
    path('mes-documents/', views.student_documents, name='documents'),
]
