from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path
from mysatnusa.response import Response
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="My satnusa platform",
      default_version='v1',
      description="API description",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', lambda r: Response.ok(message="Service Running ..")),
    path('api/auth/', include('auth.urls')),
    path('api/job_vacancy/', include('job_vacancy.urls')),
    path('api/master/', include('master.urls')),
    path('api/master_employee/', include('master_employee.urls')),
    path('api/project_list/', include('project_list.urls')),
    path('api/ai_asistant/', include('ai_asistant.urls')),
    path('api/vacancy/', include('vacancy.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)