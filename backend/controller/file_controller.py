from io import BytesIO
import zipfile

from flask import jsonify, request, send_file, session

from backend.storage.kv import get_kv, set_kv
from backend.services.delete_service import delete_node
from backend.utils.error import ErrorCode
from backend.storage.ipfs import download_file_from_ipfs
from backend.services.upload_service import upload_file
from backend.models.node import Node
from backend.controller.helpers import (
    collect_files_recursively,
    get_root_node,
    get_share_manager,
    login_required,
    route_logger,
)


def register_file_routes(app, logger):
    @app.route('/create-folder', methods=['POST'])
    @login_required
    def create_folder_route():
        data = request.get_json()
        if 'folder_path' not in data:
            return jsonify({'result': ErrorCode.INVALID_REQUEST.name}), 400
        folder_path = data.get('folder_path')
        username = session['username']

        if not folder_path or folder_path.strip("/") == "":
            return jsonify({'result': ErrorCode.INVALID_PATH.name}), 400

        parts = folder_path.strip("/").split("/")
        folder_name = parts[-1]
        parent_path = "/".join(parts[:-1])

        root = Node.from_json(get_kv(username + " ROOT"))

        parent_node = root.find_node_by_path(parent_path) if parent_path else root
        if parent_node is None or not parent_node.is_folder:
            return jsonify({'result': ErrorCode.INVALID_PATH.name}), 400

        if folder_name in parent_node.children:
            return jsonify({'result': ErrorCode.DUPLICATE_NAME.name}), 409

        new_folder = Node(name=folder_name, is_folder=True)
        parent_node.add_child(new_folder)

        set_kv(username + " ROOT", root.to_json())

        return jsonify({'result': ErrorCode.SUCCESS.name,
                        'root': root.to_json()}), 201

    @app.route('/delete', methods=['DELETE'])
    @login_required
    def delete_route():
        data = request.get_json()
        return delete_node(data)

    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_route():
        """
        Upload file to IPFS and process for RAG if it's a supported text format.
        if user wants to upload example.txt to path root/doc/example.txt. The path part in request should be root/doc
        """
        if 'file' not in request.files or 'path' not in request.form:
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        path = request.form['path']
        username = session['username']
        file = request.files['file']
        
        skip_flag = request.form.get('skip_ai_processing', 'false')
        skip_ai_processing = skip_flag.lower() == 'true'

        response_data, status_code = upload_file(file, path, username, skip_ai_processing)
        return jsonify(response_data), status_code

    @app.route('/download', methods=['POST'])
    @login_required
    def download_route():
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'message': ErrorCode.INVALID_PATH.name}), 400

        path = data['path']
        username = session['username']
        is_shared = data.get('is_shared', False)

        if is_shared:
            share_manager = get_share_manager(username)
            target_node = share_manager.resolve_shared_node(path, get_root_node)
        else:
            root = get_root_node(username)
            if not root:
                return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404
            target_node = root.find_node_by_path(path)

        if target_node is None or target_node.is_folder:
            return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404

        file_obj = target_node.file_obj
        if not file_obj:
            return jsonify({'message': ErrorCode.FILE_NOT_FOUND.name}), 404

        file_content = download_file_from_ipfs(file_obj.cid)
        if not file_content or not file_content.get("success"):
            return jsonify({'message': ErrorCode.IPFS_ERROR.name if file_content is None else file_content.get('message', ErrorCode.IPFS_ERROR.name)}), 500

        file_stream = BytesIO(file_content["file"].getvalue())
        file_stream.seek(0)

        return send_file(
            file_stream,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=file_obj.filename
        )

    @app.route('/download-zip', methods=['POST'])
    @login_required
    def download_zip_route():
        """Download a folder as a ZIP file."""
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'message': ErrorCode.INVALID_PATH.name}), 400

        path = data['path']
        username = session['username']
        is_shared = data.get('is_shared', False)

        if is_shared:
            share_manager = get_share_manager(username)
            target_node = share_manager.resolve_shared_node(path, get_root_node)
        else:
            root = get_root_node(username)
            if not root:
                return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404
            target_node = root.find_node_by_path(path)

        if target_node is None:
            return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404

        if not target_node.is_folder:
            return jsonify({'message': 'Path is not a folder'}), 400

        files_to_zip = collect_files_recursively(target_node)

        if not files_to_zip:
            return jsonify({'message': 'Folder is empty'}), 400

        zip_buffer = BytesIO()

        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for relative_path, file_obj in files_to_zip:
                    file_content = download_file_from_ipfs(file_obj.cid)

                    if file_content and file_content.get("success"):
                        zip_file.writestr(relative_path, file_content["file"].getvalue())
                    else:
                        route_logger.warning(f"Failed to download file: {relative_path}")

            zip_buffer.seek(0)

            folder_name = path.split('/')[-1] if path else 'files'

            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{folder_name}.zip"
            )

        except Exception as e:
            route_logger.error(f"Error creating ZIP file: {str(e)}")
            return jsonify({'message': 'Failed to create ZIP file'}), 500
