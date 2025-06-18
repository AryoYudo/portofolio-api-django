import json
from django.db import connection, transaction
from mysatnusa.response import Response
from django.views.decorators.csrf import csrf_exempt
from mysatnusa.middleware import jwtRequired
from django.core.paginator import Paginator
from django.urls import reverse
from common.pagination_helper import paginate_data
from common.transaction_helper import *
from common.export_excel import export_excel
import datetime
import environ
import jwt
import os
from rest_framework.decorators import api_view
from rest_framework import serializers
from rest_framework.response import Response as DRFResponse
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from operator import itemgetter
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env()

@csrf_exempt
def list_loker(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            status_id = request.GET.get('status_id')

            filters = {}
            if status_id:
                filters["status_id"] = status_id

            data = get_data(
                table_name="v_job",
                columns=["job_uuid", "position_job", "short_description", "status_name", "status_id"],
                filters=filters
            )

            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
