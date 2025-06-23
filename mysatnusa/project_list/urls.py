from django.urls import path

from . import views

urlpatterns = [
    path('list_data_project', views.list_data_project, name='list_data_project'),
    path('insert_project', views.insert_project, name='insert_project'),
    path('update_project/<str:project_uuid>', views.update_project, name='update_project'),
    path('delete_project/<str:project_uuid>', views.delete_project, name='delete_project'),
    path('list_project', views.list_project, name='list_project'),
    path('detail_project/<str:project_uuid>', views.detail_project, name='detail_project'),
] 