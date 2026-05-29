from django.shortcuts import redirect
from django.urls import path

from . import views


app_name = 'recruitment'


def _index(request):
    return redirect('recruitment:step', step=1)


urlpatterns = [
    path('', _index, name='index'),
    path('etape/<int:step>/', views.RecruitmentStepView.as_view(), name='step'),
    path('rouvrir/', views.RecruitmentReopenView.as_view(), name='reopen'),
    path('recapitulatif/', views.RecruitmentRecapView.as_view(), name='recap'),
]
