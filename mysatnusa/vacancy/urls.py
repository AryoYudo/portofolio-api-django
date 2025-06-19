from django.urls import path

from . import views

urlpatterns = [
    path('list_lowongan', views.list_lowongan, name='list_lowongan'),
    path('detail_lowongan/<str:job_uuid>', views.detail_lowongan, name='detail_lowongan'),
    path('applicants', views.applicants, name='applicants'),
    path('list_applicants', views.list_applicants, name='list_applicants'),
] 