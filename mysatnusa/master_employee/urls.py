from django.urls import path

from . import views

urlpatterns = [
    path('list_master_employee', views.list_master_employee, name='list_master_employee'),
    path('list_employee', views.list_employee, name='list_employee'),
    path('add_master_employee', views.add_master_employee, name='add_master_employee'),
    path('update_employee/<str:employee_uuid>', views.update_employee, name='update_employee'),
    path('delete_employee/<str:employee_uuid>', views.delete_employee, name='delete_employee'),
] 