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
def master_employee(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="employee_list", columns=["employee_uuid", "employee_status_id", "employee_name", "employee_position_id"], filters={"employee_status_id": 1})
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def master_internship(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="employee_list", columns=["employee_uuid", "employee_status_id", "employee_name", "employee_position_id"], filters={"employee_status_id": 2})
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def master_category(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="m_category", columns=["m_category_uuid", "category_name"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def master_position(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="m_position", columns=["position_uuid", "position_name"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def master_technology(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="m_technology", columns=["m_technology_uuid", "technology_name"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def master_status_member(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="status_member", columns=["status_id", "status_name"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
# # @jwtRequired
# @csrf_exempt
# def get_knowledge_data(request):
#     try:
#         validate_method(request, "GET")
#         with transaction.atomic():
            
#             projects = []
            
#             projects_list = get_data("projects", columns="project_id, title, short_description, description")
#             for item in projects_list:
#                 project_id = item.get("project_id")
                
#                 technology = []
#                 technology_id = get_data("technology_project", columns=["technology_id"], filters={"project_id": project_id})
#                 for t in technology_id:
#                     tech = get_value("m_technology", column_name="technology_name", filters={"technology_id": t.get("technology_id")})
#                     technology.append({ tech })
                
#                 category_name = []
#                 category_id = get_data("category_project", columns=["category_id"], filters={"project_id": project_id})
#                 for c in category_id:
#                     category = get_value("m_category", column_name="category_name", filters={"category_id": c.get("category_id")})
#                     category_name.append({ category })
                
                
#                 employee_name = []
#                 employee_id = get_data("member_project", columns=["employee_id"], filters={"project_id": project_id})
#                 for e in employee_id:
#                     category = get_value("m_category", column_name="category_name", filters={"category_id": c.get("category_id")})
                    
                
                
                
                
#             return Response.ok(data=projects, message="List data telah tampil", messagetype="S")
#     except Exception as e:
#         traceback.print_exc()
#         return Response.badRequest(request, message=str(e), messagetype="E")