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

@jwtRequired
@csrf_exempt
def list_job(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            search = request.GET.get('search')
            
            rules = {
                'search': 'string',
            }

            validation_errors = validate_request(request.GET, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")
            
            data = get_data(table_name="job", columns=["job_uuid", "position_job", "short_description", "available_until", "status_id", "created_at", "description", "job_picture"], search=search, search_columns=["position_job", "short_description"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def add_job(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()
            
            rules = {
                'position_job': 'required|string|min:3|max:62',
                'short_description': 'required|string|min:3|max:255',
                'description': 'required|string|min:3|max:1024',
                'available_until': 'required',
                'status_id': 'int',
            }

            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            available_until = datetime.datetime.strptime(json_data.get("available_until"), '%d-%m-%Y').date()
            
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
            files = request.FILES.getlist('picture')
            folder = 'job_images/'
            job_picture = None
            if files:
                file = files[0]
                filename = fs.save(folder + file.name, file)
                file_url = fs.url(filename)
                job_picture = request.build_absolute_uri(file_url)

            job_id = insert_get_id_data(
                table_name="job",
                data={
                    "position_job": json_data.get("position_job"),
                    "short_description": json_data.get("short_description"),
                    "available_until": available_until,
                    "status_id": json_data.get("status_id"),
                    "job_picture": job_picture,
                    "description": json_data.get("description"),
                },
                column_id="job_id"
            )

            job_uuid = first_data( table_name="job", columns=["job_uuid"], filters={"job_id": job_id} )
            return Response.ok(data=job_uuid, message="Added!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def update_job(request, job_uuid):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()
            job_id = get_value('job', filters={'job_uuid': job_uuid}, column_name='job_id')
            
            if not exists_data('job', filters={"job_id": job_id}):
                return Response.badRequest(request, message="Job Tidak Ditemukan", messagetype="E")

            rules = {
                'position_job': 'required|string|min:3|max:62',
                'short_description': 'required|string|min:3|max:255',
                'description': 'required|string|min:3|max:1024',
                'available_until': 'required',
                'status_id': 'int',
            }
            
            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")
            
            available_until = datetime.datetime.strptime(json_data.get("available_until"), '%d-%m-%Y').date()

            job_picture = None
            if request.FILES:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                files = request.FILES.getlist('picture')
                folder = 'employee_images/'
                if files:
                    file = files[0]
                    filename = fs.save(folder + file.name, file)
                    file_url = fs.url(filename)
                    job_picture = request.build_absolute_uri(file_url)

            update_data(
                table_name="job",
                data={
                    "position_job": json_data.get("position_job"),
                    "short_description": json_data.get("short_description"),
                    "available_until": available_until,
                    "status_id": json_data.get("status_id"),
                    "job_picture": job_picture,
                    "description": json_data.get("description"),
                },
                filters={"job_id": job_id},
            )

            return Response.ok(data=job_uuid, message="Job berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")

@csrf_exempt
def delete_job(request, job_uuid):
    try:
        validate_method(request, "DELETE")
        with transaction.atomic():
            job_id = get_value('job', filters={'job_uuid': job_uuid}, column_name='job_id')
            
            delete_data("job", filters={"job_id": job_id})

            return Response.ok(data=job_uuid, message="Project berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")


