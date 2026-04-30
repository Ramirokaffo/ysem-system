from django.urls import path

from .views import *

app_name = 'payments'
urlpatterns = [
    path('', PaymentListView.as_view(), name='payments_list'),
    path('create/', payment_create, name='payment_create'),
    path('<int:pk>/', payment_detail, name='payment_detail'),
    path('<int:pk>/recu/', payment_receipt, name='payment_receipt'),
    path('ajax/student-search/', payment_student_search, name='payment_student_search'),
    path('ajax/installment-summary/', payment_installment_summary, name='payment_installment_summary'),

    path('statut-paiement/', PaymentStatusView.as_view(), name='payment_status'),
    path('statut-paiement/<str:pk>/', PaymentStatusStudentDetailView.as_view(), name='payment_status_student_detail'),

]