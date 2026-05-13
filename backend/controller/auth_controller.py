import hashlib
import json

from flask import jsonify, request, session

from backend.RSDB_kv_service import get_kv, set_kv
from backend.error import ErrorCode
from backend.user_authentication_service import login, sign_up
from backend.controller.helpers import get_resolved_share_list, login_required


def register_auth_routes(app, logger):
    @app.route('/login', methods=['POST'])
    def login_route():
        data = request.get_json()
        username = data['username']
        password = data['password']

        result = login(username, password)

        if result == ErrorCode.SUCCESS:
            session['username'] = username
            session.permanent = True
            root_json_str = get_kv(username + " ROOT")
            root_json = json.loads(root_json_str)
            share_list = get_resolved_share_list(username)

            response = jsonify({
                'message': result.name,
                'result': result.name,
                'root': root_json,
                'share_list': share_list
            })

            logger.info(f"Response headers: {dict(response.headers)}")
            return response, 200

        return jsonify({'message': result.name, 'result': result.name}), 401

    @app.route('/signup', methods=['POST'])
    def signup_route():
        data = request.get_json()
        username = data['username']
        password = data['password']
        result = sign_up(username, password)
        if result == ErrorCode.SUCCESS:
            return jsonify({
                'ok': "true",
                'message': result.name,
                'result': result.name
            }), 200

        return jsonify({'message': result.name, 'result': result.name}), 401

    @app.route('/delete-user', methods=['DELETE'])
    @login_required
    def delete_user_route():
        data = request.get_json()
        username = session['username']
        password = data['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if hashed_password != get_kv(username):
            return jsonify({'message': ErrorCode.INCORRECT_PASSWORD.name}), 401

        set_kv(username, "\n")
        set_kv(username + " ROOT", "\n")
        set_kv(username + " SHARE_MANAGER", "\n")

        session.pop('username')

        return jsonify({'message': ErrorCode.SUCCESS.name}), 200

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout_route():
        session.pop('username', None)
        return jsonify({'message': ErrorCode.SUCCESS.name}), 200

    @app.route('/auth-status', methods=['GET'])
    def auth_status():
        """Check if user has a valid session and return user data if authenticated"""
        if 'username' in session:
            username = session['username']
            try:
                root_json = get_kv(username + " ROOT")
                if root_json and root_json != "\n":
                    return jsonify({
                        'authenticated': True,
                        'username': username,
                        'root': json.loads(root_json),
                        'share_list': get_resolved_share_list(username)
                    }), 200
                else:
                    session.pop('username', None)
                    return jsonify({'authenticated': False}), 401
            except Exception as e:
                logger.error(f"Error checking auth status: {e}")
                session.pop('username', None)
                return jsonify({'authenticated': False}), 401

        return jsonify({'authenticated': False}), 401
