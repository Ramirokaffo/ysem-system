from django.urls import path

from . import views


app_name = 'emails'

urlpatterns = [
    path('composer/', views.compose_email, name='compose'),
]
