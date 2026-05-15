from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.student_login, name='login'),
    path('connexion/', views.student_login, name='login'),
    path('deconnexion/', views.student_logout, name='logout'),
    path('changer-mot-de-passe/', views.student_change_password, name='change_password'),
    path('tableau-de-bord/', views.student_dashboard, name='dashboard'),
    path('mes-documents/', views.student_documents, name='documents'),
    path(
        'mes-documents/<int:pk>/certificat-inscription/',
        views.registration_certificate_download,
        name='registration_certificate_download',
    ),
    path('ma-situation-financiere/', views.student_finances, name='finances'),
    path(
        'ma-situation-financiere/recu/<int:pk>/',
        views.student_payment_receipt_download,
        name='payment_receipt_download',
    ),
    path(
        'ma-situation-financiere/releve/<int:academic_year_id>/',
        views.student_account_statement_download,
        name='account_statement_download',
    ),
]
