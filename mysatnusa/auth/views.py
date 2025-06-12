import json
from django.conf import settings
from django.db import connection, transaction
from mysatnusa.response import Response
from django.views.decorators.csrf import csrf_exempt
from mysatnusa.middleware import jwtRequired
from django.core.paginator import Paginator
from django.urls import reverse
from common.transaction_helper import *
from common.format_date import format_date
import datetime
import environ
from pprint import pprint
import jwt
import bcrypt
import os
import traceback
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
import uuid
import secrets
from django.utils.crypto import get_random_string
from jwt import ExpiredSignatureError, InvalidTokenError
from django.core.cache import cache
import hmac
import hashlib
import time

from django.contrib.auth import authenticate, login

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env()


@csrf_exempt
def login(request):
    validate_method(request, "POST")
    json_data = json.loads(request.body)
    badge = json_data['badge']
    password = json_data['password']
    try:
        with transaction.atomic():
            data_db = get_data(
                table_name="users", 
                filters={"badge": badge}, 
                columns="badge, password, uuid, user_name"
            )

            if not isinstance(data_db, list) or not data_db:
                return Response.badRequest(
                    request, 
                    message='Badge tidak ditemukan atau belum terdaftar. Silakan hubungi Admin.', 
                    messagetype='E'
                )

            user_data = data_db[0]

            stored_hashed_password = user_data['password'].encode('utf-8')
            provided_password = password.encode('utf-8')
            
            if not bcrypt.checkpw(provided_password, stored_hashed_password):
                return Response.badRequest( request, message='Password salah. Silakan coba lagi.', messagetype='E' )

            if bcrypt.checkpw(provided_password, stored_hashed_password):
                access_token = create_jwt_token(user_data['uuid'], user_data['badge'], user_data['user_name'])
                refresh_token = create_jwt_token(user_data['uuid'], user_data['badge'], user_data['user_name'], 2880)

                user_data.pop('password', None)
                user_data['accessToken'] = access_token
                user_data['refreshToken'] = refresh_token

                # Convert any bytes values to strings
                user_data = {
                    key: (value.decode('utf-8') if isinstance(value, bytes) else value) 
                    for key, value in user_data.items()
                }

                return Response.ok(data=user_data, message="Berhasil masuk!", messagetype='S')
            else:
                return Response.badRequest(request, message='Invalid username or password', messagetype='E')

    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=f'Terjadi kesalahan: {str(e)}')


def create_jwt_token(uuid, badge, user_name, exp=settings.JWT_AUTH_EXPIRY):
    # Define expiration time (e.g., 30 minutes)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=exp)

    payload = {
        'uuid': str(uuid),
        'badge_no': badge,
        'fullname': user_name,
        'exp': expiration_time
    }

    # Encode the token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def create_qr_login_token(user_uuid, user_badge, user_name):
    # Define expiration time (e.g., 5 minutes for one-time login)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    
    # Unique identifier to make the token one-time use
    token_id = str(uuid.uuid4())

    payload = {
        'uuid': str(user_uuid),
        'badge_no': user_badge,
        'fullname': user_name,
        'token_id': token_id,  # Add a unique token ID
        'exp': expiration_time
    }

    # Encode the token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def verify_qr_login_token(token):
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

        # Check if token_id has been used already
        token_id = payload.get('token_id')
        if not token_id or cache.get(f'used_qr_token:{token_id}'):
            return False, "Invalid or already used token"

        # Mark token_id as used
        cache.set(f'used_qr_token:{token_id}', True, timeout=300)  # Expires in 5 minutes

        # Return user info from the token
        return True, {
            'user_uuid': payload.get('uuid'),
            'badge_id': payload.get('badge_no'),
            'fullname': payload.get('fullname')
        }
    except ExpiredSignatureError:
        return False, "Token has expired"
    except InvalidTokenError:
        return False, "Invalid token"
    
@csrf_exempt
def generate_qr_token(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            unique_token = secrets.token_urlsafe(16) + str(uuid.uuid4()) +  get_random_string(32)
            insert_data(
                table_name="sso.logins",
                data={
                    "login_token":  unique_token,
                    "created_at": datetime.datetime.now()
                }
            )
            
            return Response.ok(data={'unique_token' : unique_token}, message="Generate QR Token!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def delete_qr_token(request):
    try:
        validate_method(request, "DELETE")
        with transaction.atomic():
            json_data = json.loads(request.body)
            delete_data(
                table_name="sso.logins",
                filters={
                    "login_token": json_data['unique_token'],
                }
            )
            
            return Response.ok(data={'unique_token' : json_data['unique_token']}, message="QR Token Deleted!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")
    
@csrf_exempt
def login_qr(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = json.loads(request.body)
            login_token = first_data(
                table_name="sso.logins",
                filters={
                    "login_token": json_data['unique_token']
                }
            )
            
            if not login_token:
                return Response.badRequest(request, message='Invalid QR Token', messagetype='E', status=401)
            
            users = first_data(
                table_name="sso.v_view_all_user",
                filters={
                    "user_badge": login_token['login_badge']
                }
            )
            
            if users:
                token_qr = create_qr_login_token(users['user_uuid'], users['user_badge'], users['user_name'])
                
                verify = verify_qr_login_token(token_qr)

                if verify[0] == False:
                    return Response.badRequest(request, message='Invalid QR Token', messagetype='E', status=401)
                
                # check badge apakah ada di sso.v_view_all_user
                data_db = get_data(
                    table_name="sso.v_view_all_user", filters={"user_badge":verify[1]['badge_id']}, 
                    columns="user_badge, user_name, user_password, is_active, user_uuid"
                    )
                
                if not isinstance(data_db, list) or not data_db:
                    return Response.badRequest(request, message='invalid username', messagetype='E')
                
                user_data = data_db[0]  # Get the first user dictionary
                
                if user_data['is_active'] == False:
                    return Response.badRequest(request, message='User is not active', messagetype='E')
                
                access_token = create_jwt_token(verify[1]['user_uuid'], verify[1]['badge_id'], verify[1]['fullname'])
                refresh_token = create_jwt_token(verify[1]['user_uuid'], verify[1]['badge_id'], verify[1]['fullname'], 2880)
                
                # Remove the user_password from user_data
                user_data.pop('user_password', None)
                user_data['access_token'] = access_token
                user_data['refresh_token'] = refresh_token

                # Remove the login_token from login_token
                delete_data(
                    table_name="sso.logins",
                    filters={
                        "login_token": json_data['unique_token'],
                    }
                )
                return Response.ok(data=user_data, message="Berhasil masuk!", messagetype='S')
                
            else:
                return Response.badRequest(request, message="Data badge user tidak tampil!", messagetype="E")
    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")    

@csrf_exempt
def refresh_access_token(request):
    try:
        # Get the refresh token from the request (e.g., from POST body)
        json_data = json.loads(request.body)
        refresh_token = json_data['refresh_token']
        

        if not refresh_token:
            return Response.badRequest(request, message="Refresh token is required", messagetype="E")

        # Decode the refresh token
        try:
            refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])

         
            # Generate a new access token using the information from the refresh token
            user_uuid = refresh_payload.get('id')

            # Assuming user_badge and user_name are fetched from the database or from user data
            new_tokens = create_jwt_token(
                user_uuid=user_uuid,
                user_badge=None,  # Optional: Fetch from the database if needed
                user_name=None    # Optional: Fetch from the database if needed
            )

            # Return the new access token (optionally include refresh token)
            return Response.ok(data=new_tokens, message="Data user telah tampil!", messagetype="S")

        except ExpiredSignatureError:
            return Response.badRequest(request, message='Refresh token has expired', messagetype='E', status=401)
        except InvalidTokenError:
            return Response.badRequest(request, message='Invalid refresh token', messagetype='E', status=401)

    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")    
    

@csrf_exempt
def logout(request):
    try:
        validate_method(request, "POST")
        json_data = json.loads(request.body)
        token = json_data['access_token']
        
        if not token:
            return Response.badRequest(request, message='Token is required for logout', messagetype='E', status=401)

        invalidate_token(token)
        
        return Response.ok(message="Logout Successfull", messagetype="S")
    
    except Exception as e:
        log_exception(request, e)
        print(traceback.format_exc())
        # return Response.badRequest(request, message='An error occurred: {str(e)}', messagetype='E', status=401)
        return Response.badRequest(request, message=str(e), messagetype="E", status=500)    
    
TOKEN_BLACKLIST = set()

def invalidate_token(token):
    TOKEN_BLACKLIST.add(token)
    
@csrf_exempt
def scan_qr_token(request, qr_token):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
            json_data = json.loads(request.body)
            
            rules = {
                'badge_no': 'required|string|min:4|max:8',
            }

            validation_errors = validate_request(json_data, rules)
            if validation_errors:
                return Response.badRequest(request, message=validation_errors, messagetype="E")

            data_db = get_data(
                table_name="sso.v_view_all_user",
                filters={"user_badge":json_data['badge_no']}, 
                columns="user_badge, user_name, user_password, is_active, user_uuid"
            )
                
            if not isinstance(data_db, list) or not data_db:
                return Response.badRequest(request, message='Invalid credentials. You are not registered with HR, please contact HR', messagetype='E')
                
            user_data = data_db[0]  # Get the first user dictionary
            
            if user_data['is_active'] == False:
                return Response.badRequest(request, message='User is inactive. You are not yet active, please contact the administrator.', messagetype='E')
            
            if not exists_data(table_name="sso.logins", filters={"login_token": qr_token}):
                return Response.badRequest(request, message="QR Token Tidak ditemukan!", messagetype="E")
            
            check_data = first_data(table_name="sso.logins", filters={"login_token": qr_token})
            
            if check_data['login_badge'] != None:
                return Response.badRequest(request, message="QR Token sudah discan sebelumnya!", messagetype="E")
            
            update_data(
                table_name="sso.logins",
                data={
                    "login_badge":  json_data['badge_no'],
                },
                filters={
                    "login_token": qr_token,
                }
            )
            
            return Response.ok(data={'unique_token' : qr_token}, message="Berhasil Scan QR Token!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")

@csrf_exempt
def generate_api_key(request):
    try:
        validate_method(request, "POST")
        with transaction.atomic():
    
            SECRET_KEY = "MySatnusa"
            
            # Menentukan periode 6 bulan
            current_month = datetime.datetime.utcnow().month
            year = datetime.datetime.utcnow().year
            period = f"{year}-{'01' if current_month <= 6 else '07'}"  # Januari-Juni -> periode 01, Juli-Desember -> periode 07

            # Membuat API key yang diharapkan
            expected_api_key = hmac.new(SECRET_KEY.encode(), period.encode(), hashlib.sha256).hexdigest()
            
            headers = {
                "X-API-KEY": expected_api_key,
            }
        return Response.ok(data=headers, message="Berhasil Generate API-KEY!", messagetype="S")
    except Exception as e:
        log_exception(request, e)
        return Response.badRequest(request, message=str(e), messagetype="E")