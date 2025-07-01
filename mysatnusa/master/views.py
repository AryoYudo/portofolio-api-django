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
            
            data = get_data(table_name="employee_list", columns=["employee_id","employee_uuid", "employee_status_id", "employee_name", "employee_position_id"])
            
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
    
@csrf_exempt
def master_category(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="m_category")
            
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
            
            data = get_data(table_name="m_position")
            
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
            
            data = get_data(table_name="m_technology")
            
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
    
@jwtRequired
@csrf_exempt
def master_job_relate(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            data = get_data(table_name="job")
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def get_knowledge_data(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            
            information_project = []

            projects_list = get_data( "projects", columns="project_id, title, short_description, description, start_project, finish_project" )
            for p in projects_list:
                pid = p["project_id"]
                information_project.append({
                    **p,
                    "project_creator": get_data( "v_employee_participant", columns=["employee_name", "employee_status", "employee_position"], filters={"project_id": pid} ),
                    "category_project": [c["category_name"] for c in get_data( "v_project_categories", columns=["category_name"], filters={"project_id": pid} )],
                    "technology_project": [t["technology_name"] for t in get_data( "v_technology_project", columns=["technology_name"], filters={"project_id": pid} )]
                })


            information_employee_departement = get_data("v_employee", columns=["employee_name", "employee_status", "employee_position"])
            
            information_job = []
            job = get_data("v_job", columns=["position_job", "short_description", "available_until", "status_name"])
            for i in job:
                information_job.append({
                    "position_name": i.get("position_job"),
                    "description": i.get("short_description"),
                    "available": i.get("available_until"),
                    "status": i.get("status_name")
                })
                
            data = {
                "information_project": information_project,
                "information_employee_departement": information_employee_departement,
                "information_job": information_job,
            }
                
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")