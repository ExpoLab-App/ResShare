from io import BytesIO
import mimetypes
import zipfile

from flask import jsonify, request, send_file, session

from backend.services.RSDB_kv_service import get_kv, set_kv
from backend.services.delete_service import delete_node
from backend.utils.error import ErrorCode
from backend.models.file import File
from backend.services.ipfs_service import add_file_to_cluster, download_file_from_ipfs
from backend.models.node import Node
from backend.services.rag_persistence import (
    RAGPersistenceResult,
    persist_root_with_rag_rollback,
)
from backend.controller.helpers import (
    collect_files_recursively,
    get_root_node,
    get_share_manager,
    login_required,
    route_logger,
)
from backend.utils.util import validate_file_size
from backend.services.rag_utils import get_rag_manager

FILE_SIZE_LIMIT = 1024 * 1024  # 1 MB limit


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
        if user want to upload example.txt to path root/doc/example.txt. The path part in request should be root/doc
        """
        if 'file' not in request.files or 'path' not in request.form:
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        path = request.form['path']
        username = session['username']
        file = request.files['file']
        raw_skip_flag = request.form.get('skip_ai_processing', 'false')
        skip_ai_processing = raw_skip_flag.lower() == 'true'
        route_logger.info(f"Upload request: user={username}, file={file.filename if file else 'N/A'}, skip_ai_processing_raw='{raw_skip_flag}', parsed={skip_ai_processing}")

        if file.filename == '':
            return jsonify({'message': ErrorCode.INVALID_REQUEST.name}), 400

        filename = file.filename
        file_stream = BytesIO(file.read())

        file_size = file_stream.getbuffer().nbytes

        is_valid, error_message = validate_file_size(file_size, FILE_SIZE_LIMIT)
        if not is_valid:
            return jsonify({'message': error_message}), 413

        cid = add_file_to_cluster(file_stream, filename)

        if cid is None:
            return jsonify({'message': ErrorCode.IPFS_ERROR.name}), 500

        root = Node.from_json(get_kv(username + " ROOT"))
        target_node = root.find_node_by_path(path)

        if target_node is None:
            return jsonify({'message': ErrorCode.NODE_NOT_FOUND.name}), 404

        supported_extensions = {'pdf', 'docx', 'txt'}
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        should_index = not skip_ai_processing and file_extension in supported_extensions
        file_obj = File(
            cid,
            file_size,
            filename,
            mime_type=file.mimetype or mimetypes.guess_type(filename)[0],
            rag_status="pending" if should_index else "skipped",
        )
        result = target_node.add_child(Node(filename, False, file_obj=file_obj))

        if result != ErrorCode.SUCCESS:
            return jsonify({'message': result.name}), 400

        rag_success = False
        rag_skipped = False
        rag_manager = None

        if should_index:
            try:
                file_stream.seek(0)
                file_content = file_stream.read()
                normalized_parent = path.strip("/")
                if normalized_parent == "root":
                    normalized_parent = ""
                elif normalized_parent.startswith("root/"):
                    normalized_parent = normalized_parent[len("root/"):]
                document_path = "/".join(
                    part for part in (normalized_parent, filename) if part
                )

                rag_manager = get_rag_manager()
                rag_result = rag_manager.process_file_for_rag(
                    file_content,
                    filename,
                    username,
                    cid,
                    file_obj.document_id,
                    document_path,
                )
                rag_success = rag_result.success

                if rag_success:
                    file_obj.mark_rag_ready(
                        rag_result.chunk_count,
                        rag_manager.embedding_model_name,
                    )
                    route_logger.info(
                        "Successfully processed %s for RAG for user %s",
                        filename,
                        username,
                    )
                else:
                    file_obj.mark_rag_failed(
                        rag_result.error,
                        rag_manager.embedding_model_name,
                    )
                    route_logger.warning(
                        "Failed to process %s for RAG for user %s",
                        filename,
                        username,
                    )

            except Exception as e:
                route_logger.error(f"RAG processing error for {filename}: {e}")
                rag_success = False
                file_obj.mark_rag_failed(str(e), "gemini-embedding-001")

        elif skip_ai_processing:
            rag_skipped = True
            route_logger.info(
                "RAG processing skipped for %s for user %s (AI mode disabled)",
                filename,
                username,
            )
        else:
            rag_skipped = True
            route_logger.info(f"RAG processing skipped for unsupported file {filename}")

        persistence_result = persist_root_with_rag_rollback(
            username,
            root.to_json(),
            rag_manager=rag_manager if rag_success else None,
            indexed_document_id=file_obj.document_id if rag_success else None,
        )
        if persistence_result != RAGPersistenceResult.SUCCESS:
            return jsonify({'message': persistence_result.value}), 503

        response_data = {
            'message': ErrorCode.SUCCESS.name,
            'root': root.to_json(),
            'rag_processed': rag_success,
            'rag_skipped': rag_skipped,
            'rag_status': file_obj.rag_status,
            'skip_ai_processing': skip_ai_processing
        }

        return jsonify(response_data), 200

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
