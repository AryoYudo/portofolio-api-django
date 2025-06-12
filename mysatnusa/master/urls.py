from django.urls import path

from . import views

urlpatterns = [
    path('master_employee', views.master_employee, name='master_employee'),
    path('master_internship', views.master_internship, name='master_internship'),
    path('master_category', views.master_category, name='master_category'),
    path('master_position', views.master_position, name='master_position'),
    path('master_technology', views.master_technology, name='master_technology'),
    path('master_status_member', views.master_status_member, name='master_status_member'),
]