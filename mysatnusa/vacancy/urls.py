from django.urls import path

from . import views

urlpatterns = [
    path('list_loker', views.list_loker, name='list_loker'),
] 