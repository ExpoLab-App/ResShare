from flask import jsonify, request, session

from backend.RSDB_kv_service import get_kv, set_kv
from backend.error import ErrorCode
from backend.node import Node
from backend.controller.helpers import (
    get_resolved_share_list,
    get_root_node,
    get_share_manager,
    login_required,
)


def register_share_routes(app, logger):
    @app.route('/share', methods=['POST'])
    @login_required
    def share_route():
        data = request.get_json()
        if 'target' not in data:
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400
        username = session['username']
        target_username = data['target']

        if not get_kv(target_username).strip():
            return jsonify({'message': ErrorCode.INVALID_USERNAME.name}), 400

        path = data.get('path')
        if not path and 'node' in data:
            try:
                node_payload = Node.from_json(data['node'])
                path = node_payload.name
            except Exception:
                return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        if not path:
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        owner_root = get_root_node(username)
        if not owner_root:
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        target_node = owner_root.find_node_by_path(path)
        if not target_node:
            return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404

        if target_node.name == "root" or path.strip("/") in ["", "root"]:
            return jsonify({'message': ErrorCode.SHARE_ROOT.name}), 400

        target_sm = get_share_manager(target_username)
        result = target_sm.receive(username, path, target_node.is_folder)
        if result != ErrorCode.SUCCESS:
            return jsonify({'message': result.name}), 400

        set_kv(target_username + " SHARE_MANAGER", target_sm.to_json())

        return jsonify({'message': ErrorCode.SUCCESS.name}), 200

    @app.route('/shared', methods=['GET'])
    @login_required
    def shared_items():
        """Return the latest shared items for the authenticated user."""
        username = session['username']
        return jsonify({'share_list': get_resolved_share_list(username)}), 200
