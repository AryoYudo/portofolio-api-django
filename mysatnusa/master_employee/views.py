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
def list_master_employee(request):
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
            
            data = get_data(table_name="v_employee", columns=["employee_uuid", "employee_name", "employee_picture", "employee_status", "employee_position", "employee_position_id"], search=search, search_columns=["employee_name"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def add_master_employee(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()

            rules = {
                'employee_status_id': 'required',
                'employee_name': 'required|string|min:3|max:62',
                'employee_position_id': 'required',
            }

            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            employee_picture = None
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
            files = request.FILES.getlist('picture')
            folder = 'employee_images/'
            if files:
                file = files[0]
                filename = fs.save(folder + file.name, file)
                file_url = fs.url(filename)
                employee_picture = request.build_absolute_uri(file_url)

            employee_id = insert_get_id_data(
                table_name="employee_list",
                data={
                    "employee_picture": employee_picture,
                    "employee_status_id": json_data.get("employee_status_id"),
                    "employee_name": json_data.get("employee_name"),
                    "employee_position_id": json_data.get("employee_position_id"),
                    "created_at": datetime.datetime.now()
                },
                column_id="employee_id"
            )

            employee_uuid = first_data( table_name="employee_list", columns=["employee_uuid"], filters={"employee_id": employee_id} )
            return Response.ok(data=employee_uuid, message="Added!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def update_employee(request, employee_uuid):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()
            employee_id = get_value('employee_list', filters={'employee_uuid': employee_uuid}, column_name='employee_id')
            if not exists_data('employee_list', filters={"employee_id": employee_id}):
                return Response.badRequest(request, message="Employee Tidak Ditemukan", messagetype="E")

            rules = {
                'employee_status_id': 'int',
                'employee_name': 'required|string|min:3|max:62',
                'employee_position_id': 'required',
            }
            
            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            employee_picture = None
            if request.FILES:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                files = request.FILES.getlist('picture')
                folder = 'employee_images/'
                if files:
                    file = files[0]
                    filename = fs.save(folder + file.name, file)
                    file_url = fs.url(filename)
                    employee_picture = request.build_absolute_uri(file_url)

            update_data(
                table_name="employee_list",
                data={
                    "employee_picture": employee_picture,
                    "employee_status_id": json_data.get("employee_status_id"),
                    "employee_name": json_data.get("employee_name"),
                    "employee_position_id": json_data.get("employee_position_id"),
                },
                filters={"employee_id": employee_id},
            )

            return Response.ok(data=employee_uuid, message="Employee berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")

@jwtRequired
@csrf_exempt
def delete_employee(request, employee_uuid):
    try:
        validate_method(request, "DELETE")
        with transaction.atomic():
            employee_id = get_value('employee_list', filters={'employee_uuid': employee_uuid}, column_name='employee_id')
            
            delete_data("employee_list", filters={"employee_id": employee_id})

            return Response.ok(data=employee_uuid, message="Project berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
    
@csrf_exempt
def list_employee(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            filters = {}
            if request.GET.get('filters'):
                filters = {
                    "employee_position_id": request.GET.get('filters')
                }

            data = get_data(
                table_name="v_employee",
                columns=[
                    "employee_uuid", "employee_name", "employee_picture",
                    "employee_status", "employee_position", "employee_position_id"
                ],
                filters=filters,
            )

            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")



