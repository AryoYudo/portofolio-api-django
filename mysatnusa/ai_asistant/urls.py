from django.urls import path

from . import views

urlpatterns = [
    path('gemini_chat_view', views.gemini_chat_view, name='gemini_chat_view'),
]