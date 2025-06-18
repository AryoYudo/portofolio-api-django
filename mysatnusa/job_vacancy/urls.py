from django.urls import path

from . import views

urlpatterns = [
    path('list_job', views.list_job, name='list_job'),
    path('add_job', views.add_job, name='add_job'),
    path('update_job/<str:job_uuid>', views.update_job, name='update_job'),
    path('delete_job/<str:job_uuid>', views.delete_job, name='delete_job'),
] 
