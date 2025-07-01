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
def list_data_project(request):
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
            
            data = get_data(table_name="projects", columns=["project_uuid", "thumbnail_project", "title", "short_description", "description"], search=search, search_columns=["title", "short_description"])
            
            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@jwtRequired
@csrf_exempt
def insert_project(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():

            json_data = request.POST.dict()

            try:
                json_data['category'] = json.loads(json_data.get('category', '[]'))
                json_data['technology'] = json.loads(json_data.get('technology', '[]'))
                json_data['member_project'] = json.loads(json_data.get('member_project', '[]'))
                json_data['job_relate'] = json.loads(json_data.get('job_relate', '[]'))
            except json.JSONDecodeError as e:
                return Response.badRequest(request, message="Format list salah: " + str(e), messagetype="E")

            rules = {
                'title': 'required|string|min:3|max:255',
                'short_description': 'required|string|min:3|max:62',
                'description': 'required|string|min:3|max:1024',
            }

            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")
            
              # Langsung parse date di sini
            start_project = json_data.get("start_project")
            finish_project = json_data.get("finish_project")

            if start_project:
                try:
                    start_project = datetime.datetime.strptime(start_project, "%Y-%m-%d").date()
                except ValueError:
                    return Response.badRequest(request, message="start_project harus format YYYY-MM-DD", messagetype="E")
            else:
                start_project = None

            if finish_project:
                try:
                    finish_project = datetime.datetime.strptime(finish_project, "%Y-%m-%d").date()
                except ValueError:
                    return Response.badRequest(request, message="finish_project harus format YYYY-MM-DD", messagetype="E")
            else:
                finish_project = None

            thumbnail_project = None
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
            files = request.FILES.getlist('picture')
            folder = 'project_thumbnails/'
            if files:
                file = files[0]
                filename = fs.save(folder + file.name, file)
                file_url = fs.url(filename)
                thumbnail_project = request.build_absolute_uri(file_url)

            project_id = insert_get_id_data(
                table_name="projects",
                data={
                    "thumbnail_project": thumbnail_project,
                    "title": json_data.get("title"),
                    "short_description": json_data.get("short_description"),
                    "description": json_data.get("description"),
                    "start_project": json_data.get("start_project"),
                    "finish_project": json_data.get("finish_project")
                },
                column_id="project_id"
            )

            for item in json_data.get("category", []):
                insert_data("category_project", {
                    "project_id": project_id,
                    "category_id": item.get("category_id"),
                })

            for item in json_data.get("technology", []):
                insert_data("technology_project", {
                    "project_id": project_id,
                    "technology_id": item.get("technology_id"),
                })

            for item in json_data.get("member_project", []):
                insert_data("member_project", {
                    "project_id": project_id,
                    "employee_id": item.get("employee_id"),
                    "employee_name": item.get("employee_name"),
                })
            
            job_relate = json_data.get("job_relate", [])
            if job_relate:
                for item in job_relate:
                    insert_data("job_relate", {
                        "project_id": project_id,
                        "job_id": item.get("job_id"),
                        "position_job": item.get("position_job"),
                        "created_at": datetime.datetime.now()
                    })

            project_uuid = first_data( table_name="projects", columns=["project_uuid"], filters={"project_id": project_id} )

            return Response.ok(data=project_uuid, message="Added!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")

@jwtRequired
@csrf_exempt
def update_project(request, project_uuid):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = request.POST.dict()
            try:
                json_data['category'] = json.loads(json_data.get('category', '[]'))
                json_data['technology'] = json.loads(json_data.get('technology', '[]'))
                json_data['member_project'] = json.loads(json_data.get('member_project', '[]'))
                json_data['job_relate'] = json.loads(json_data.get('job_relate', '[]'))
            except json.JSONDecodeError as e:
                return Response.badRequest(request, message="Format list salah: " + str(e), messagetype="E")
            
            project_id = get_value('projects', filters={'project_uuid': project_uuid}, column_name='project_id')

            if not exists_data('projects', filters={"project_id": project_id}):
                return Response.badRequest(request, message="Project tidak ditemukan", messagetype="E")

            # Validasi data field utama
            rules = {
                'title': 'required|string|min:3|max:255',
                'short_description': 'required|string|min:3|max:62',
                'description': 'required|string|min:3|max:1024',
            }
            
            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            # Handle file upload (thumbnail)
            thumbnail_project = None
            if request.FILES:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                files = request.FILES.getlist('picture')
                folder = 'project_thumbnails/'
                if files:
                    file = files[0]
                    filename = fs.save(folder + file.name, file)
                    file_url = fs.url(filename)
                    thumbnail_project = request.build_absolute_uri(file_url)

            # Update data utama project
            update_data(
                table_name="projects",
                data={
                    "thumbnail_project": thumbnail_project,
                    "title": json_data.get("title"),
                    "short_description": json_data.get("short_description"),
                    "description": json_data.get("description"),
                    "start_project": json_data.get("start_project"),
                    "finish_project": json_data.get("finish_project"),
                    "update_at": datetime.datetime.now()
                },
                filters={"project_id": project_id},
            )

            # Delete relasi lama dan insert data baru
            delete_data("category_project", filters={"project_id": project_id})
            for item in json_data.get("category", []):
                insert_data("category_project", {
                    "project_id": project_id,
                    "category_id": item.get("category_id"),
                    "update_at": datetime.datetime.now()
                })

            delete_data("technology_project", filters={"project_id": project_id})
            for item in json_data.get("technology", []):
                insert_data("technology_project", {
                    "project_id": project_id,
                    "technology_id": item.get("technology_id"),
                    "update_at": datetime.datetime.now()
                })

            delete_data("member_project", filters={"project_id": project_id})
            for item in json_data.get("member_project", []):
                insert_data("member_project", {
                    "project_id": project_id,
                    "employee_id": item.get("employee_id"),
                    "employee_name": item.get("employee_name"),
                    "update_at": datetime.datetime.now()
                })
            
            job_relate = json_data.get("job_relate", [])
            if job_relate:
                delete_data("job_relate", filters={"project_id": project_id})
                for item in json_data.get("job_relate", []):
                    insert_data("job_relate", {
                        "project_id": project_id,
                        "job_id": item.get("job_id"),
                        "position_job": item.get("position_job"),
                        "created_at": datetime.datetime.now()
                    })

            project_uuid = first_data( table_name="projects", columns=["project_uuid"], filters={"project_id": project_id} )
            return Response.ok(data=project_uuid, message="Project berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")

@csrf_exempt
def delete_project(request, project_uuid):
    try:
        validate_method(request, "DELETE")
        with transaction.atomic():
            project_id = get_value('projects', filters={'project_uuid': project_uuid}, column_name='project_id')
            
            delete_data("projects", filters={"project_id": project_id})
            delete_data("category_project", filters={"project_id": project_id})
            delete_data("technology_project", filters={"project_id": project_id})
            delete_data("member_project", filters={"project_id": project_id})   

            return Response.ok(data=project_uuid, message="Project berhasil diperbarui!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")

@csrf_exempt
def list_project(request):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            category = request.GET.get('category')
            year = request.GET.get('year')

            project_ids = None
            if category:
                related = get_data( table_name="v_project_categories", filters={"category_id": category}, columns=["project_id"] )
                project_ids = [item["project_id"] for item in related]

            sql = """
                SELECT project_id, project_uuid, thumbnail_project, title, finish_project
                FROM projects
                WHERE 1=1
            """
            params = []

            if project_ids is not None:
                if len(project_ids) == 0:
                    return Response.ok(data=[], message="Tidak ada proyek yang cocok", messagetype="S")
                sql += " AND project_id IN %s"
                params.append(tuple(project_ids))

            if year:
                sql += " AND TO_CHAR(finish_project, 'YYYY') = %s"
                params.append(str(year))

            project = execute_query(sql_query=sql, params=tuple(params))

            data = []
            for item in project:
                project_categories = get_data( table_name="v_project_categories", filters={"project_id": item.get("project_id")}, columns=["category_name", "category_id"] )
                technology_project = get_data( table_name="v_technology_project", filters={"project_id": item.get("project_id")}, columns=["technology_id", "technology_name"] )
                data.append({
                    **item,
                    "project_categories": project_categories,
                    "technology_project": technology_project
                })

            return Response.ok(data=data, message="List data telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def detail_project(request, project_uuid):
    try:
        validate_method(request, "GET")
        with transaction.atomic():
            project_id = get_value( table_name='projects', filters={'project_uuid': project_uuid}, column_name='project_id', type='UUID' )

            data_project = first_data( table_name="projects", filters={'project_id': project_id}, columns=['thumbnail_project', 'title', 'short_description', 'description', 'start_project', 'finish_project'] )
            main_project_categories = get_data( table_name="v_project_categories", filters={"project_id": project_id}, columns=["category_id", "category_name"] )
            main_technology_project = get_data( table_name="v_technology_project", filters={"project_id": project_id}, columns=["technology_id", "technology_name"] )
            employee_participant = get_data( table_name="v_employee_participant", filters={"project_id": project_id}, columns=["employee_id", "employee_name", "employee_position", "employee_status", "employee_picture"] )
            job_relate_project = get_data( table_name="v_job_relate_project", filters={"project_id": project_id}, columns=["position_job", "job_picture"] )

            others_project = []
            all_projects = get_data( table_name="projects", columns=["project_id", "project_uuid", "thumbnail_project", "title", "finish_project"] )
            for item in all_projects:
                if item.get("project_id") == project_id:
                    continue  

                if len(others_project) >= 4:
                    break
                other_categories = get_data( table_name="v_project_categories", filters={"project_id": item.get("project_id")}, columns=["category_name", "category_id"] )
                other_technologies = get_data( table_name="v_technology_project", filters={"project_id": item.get("project_id")}, columns=["technology_id", "technology_name"] )
                others_project.append({
                    **item,
                    "project_categories": other_categories,
                    "technology_project": other_technologies
                })

            data = {
                **data_project,
                "project_categories": main_project_categories,
                "technology_project": main_technology_project,
                "employee_participant": employee_participant,
                "job_relate_project": job_relate_project,
                "others_project": others_project
            }

            return Response.ok(data=data, message="Detail data concepts telah tampil", messagetype="S")
    except Exception as e:
        traceback.print_exc()
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")