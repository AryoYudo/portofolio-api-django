from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('generate_qr_token', views.generate_qr_token, name='generate_qr_token'),
    path('scan_qr_token/<str:qr_token>', views.scan_qr_token, name='scan_qr_token'),
    path('delete_qr_token', views.delete_qr_token, name='delete_qr_token'),
    path('login_qr', views.login_qr, name='login_qr'),
    path('refresh', views.refresh_access_token, name='refresh'),
    path('generate_api_key', views.generate_api_key, name='generate_api_key'),
]