from django.urls import path

from . import views

urlpatterns = [
    path('list_job', views.list_job, name='list_job'),
    path('add_job', views.add_job, name='add_job'),
    path('update_employee/<str:employee_uuid>', views.update_employee, name='update_employee'),
    path('delete_employee/<str:employee_uuid>', views.delete_employee, name='delete_employee'),
] 
