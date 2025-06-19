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
def list_lowongan(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            status_id = request.GET.get('status_id')

            filters = {}
            if status_id:
                filters["status_id"] = status_id

            data = get_data(
                table_name="v_job",
                columns=["job_uuid", "position_job", "short_description", "status_name", "status_id", "job_picture", "description"],
                filters=filters
            )

            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def detail_lowongan(request, job_uuid):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            job_id = get_value(table_name="v_job", filters={"job_uuid": job_uuid}, column_name='job_id')
            data = first_data(
                table_name="v_job",
                columns=["job_id", "job_uuid", "position_job", "short_description", "status_name", "status_id", "job_picture", "description"],
                filters={"job_id": job_id}
            )

            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def applicants(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()
            
            rules = {
                'job_id': 'required|int',
                'user_name': 'required|string|max:62',
                'email': 'required|string|min:3|max:32',
                'whatsapp_number': 'required|int',
            }

            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
            files = request.FILES.getlist('cv_file')
            folder = 'cv_file/'
            cv_file = None
            if files:
                file = files[0]
                filename = fs.save(folder + file.name, file)
                file_url = fs.url(filename)
                cv_file = request.build_absolute_uri(file_url)

            applicants_id = insert_get_id_data(
                table_name="applicants",
                data={
                    "job_id": json_data.get("job_id"),
                    "user_name": json_data.get("user_name"),
                    "email": json_data.get("email"),
                    "whatsapp_number": json_data.get("whatsapp_number"),
                    "cv_file": cv_file,
                },
                column_id="applicants_id"
            )

            applicants_uuid = first_data( table_name="applicants", columns=["applicants_uuid"], filters={"applicants_id": applicants_id} )
            return Response.ok(data=applicants_uuid, message="Added!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
