from django.urls import path

from .views import *

app_name = 'students'
urlpatterns = [
    path('etudiants/', EtudiantsView.as_view(), name='etudiants'),
    path('etudiant/<str:pk>/', etudiant_detail, name='etudiant_detail'),
    path('etudiant/<str:pk>/modifier/', etudiant_edit, name='etudiant_edit'),
    path('etudiant/<str:pk>/generer-mot-de-passe/', generate_student_external_password, name='generate_student_external_password'),
    path('mobile-upload/<str:token>/', mobile_file_upload, name='mobile_file_upload'),

]