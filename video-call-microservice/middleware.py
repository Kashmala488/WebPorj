import jwt
from flask import request, jsonify
from functools import wraps
from config import Config
import requests

def auth_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = jsonify({})
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Max-Age'] = '86400'
            return response, 200

        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = token.replace('Bearer ', '')
        try:
            decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            request.user = decoded
            
            user_response = requests.get(
                f"{Config.MERN_API_URL}/api/users/profile",
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            if user_response.status_code != 200:
                return jsonify({'error': 'User not found'}), 401
            
            user_data = user_response.json()
            user = user_data.get('data')
            if not user:
                return jsonify({'error': 'User not found'}), 401
                
            request.user = user
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
        except requests.RequestException as e:
            return jsonify({'error': f'Failed to fetch user: {str(e)}'}), 500
        return f(*args, **kwargs)
    return decorated

def restrict_to(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method == 'OPTIONS':
                response = jsonify({})
                response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
                response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
                response.headers['Access-Control-Max-Age'] = '86400'
                return response, 200
            if request.user['role'] not in roles:
                return jsonify({
                    'error': 'Access denied',
                    'userRole': request.user['role'],
                    'requiredRoles': roles
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator