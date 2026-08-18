from backend.models.node import Node
from backend.models.file import File
from backend.storage.kv import get_kv, set_kv
from backend.storage.ipfs import add_file_to_cluster
from backend.rag.vector_store import get_vector_store
from backend.rag.indexing import process_file_for_rag
import mimetypes
from io import BytesIO
from backend.utils.error import ErrorCode
from typing import Tuple, Dict, Optional
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SIZE_LIMIT = 1024 * 1024  # 1 MB limit

def upload_file(file: File, path: str, username: str, skip_ai_processing: bool) -> Tuple[Dict, int]:
    """
    Handle file upload, including RAG processing if applicable.
    File: The file to upload.
    Path: The path where the file should be uploaded.
    Username: The username of the user uploading the file.
    Skip_ai_processing: A flag indicating whether to skip AI processing.
    Returns:
        Tuple containing response data and HTTP status code.
    """
    response_data = {
            'message': ErrorCode.SUCCESS.name,
            'rag_processed': False,
            'rag_skipped': False,
            'skip_ai_processing': skip_ai_processing
        }
    if file.filename == '':
        response_data['message'] = ErrorCode.INVALID_REQUEST.name
        return response_data, 400
    filename = file.filename
    file_stream = BytesIO(file.read())
    file_size = file_stream.getbuffer().nbytes

    if file_size > FILE_SIZE_LIMIT:
        response_data['message'] = ErrorCode.EXCEED_MAX_FILE_SIZE.name
        return response_data, 413

    cid = add_file_to_cluster(file_stream, filename)

    if cid is None:
        response_data['message'] = ErrorCode.IPFS_ERROR.name
        return response_data, 500

    root = Node.from_json(get_kv(username + " ROOT"))
    target_node = root.find_node_by_path(path)

    if target_node is None:
        response_data['message'] = ErrorCode.NODE_NOT_FOUND.name
        return response_data, 404

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
        response_data['message'] = result.name
        return response_data, 400

    rag_result = None
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

            rag_result = process_file_for_rag(
                file_content,
                filename,
                username,
                cid,
                file_obj.document_id,
                document_path,
            )
            response_data['rag_processed'] = rag_result.success

            if rag_result.success:
                file_obj.mark_rag_ready(
                    rag_result.chunk_count,
                    rag_result.embedding_model_name,
                )
                logger.info(f"Successfully processed {filename} for RAG for user {username}")
            else:
                file_obj.mark_rag_failed(
                    rag_result.error,
                    rag_result.embedding_model_name,
                )
                logger.warning(f"Failed to process {filename} for RAG for user {username}: {rag_result.error}")

        except Exception as e:
            logger.error(f"RAG processing error for {filename}: {e}")
            response_data['rag_processed'] = False
            file_obj.mark_rag_failed(str(e), "gemini-embedding-001")

    elif skip_ai_processing:
        response_data['rag_skipped'] = True
        logger.info(f"RAG processing skipped for {filename} for user {username} (AI mode disabled)")
    else:
        response_data['rag_skipped'] = True
        logger.info(f"RAG processing skipped for unsupported file {filename}")

    persistence_result = persist_root_with_rag_rollback(
        username,
        root.to_json(),
        indexed_document_id=(
            file_obj.document_id if rag_result is not None and rag_result.success else None
        ),
    )
    if not persistence_result:
        response_data['message'] = ErrorCode.KV_SERVICE_ERROR.name
        return response_data, 503

    response_data.update({
        'root': root.to_json(),
        'rag_processed': rag_result.success if rag_result is not None else False,
        'rag_status': file_obj.rag_status,
    })

    return response_data, 200
    

def persist_root_with_rag_rollback(
    username,
    root_json,
    indexed_document_id: Optional[str]=None,
) -> bool:
    """Persist the final root and remove new vectors if that write fails."""
    if set_kv(username + " ROOT", root_json):
        return True

    logger.error(f"Failed to persist final file metadata for user {username}")
                
    if indexed_document_id is None:
        return False

    #surely there is a better way to do this than creating a new instance every time
    vector_store = get_vector_store()

    try:
        rollback_succeeded = vector_store.delete_documents(
            username,
            [indexed_document_id],
        )
    except Exception as exc:
        logger.error(
            "Failed to roll back indexed document %s for user %s: %s",
            indexed_document_id,
            username,
            exc,
        )
        rollback_succeeded = False

    if not rollback_succeeded:
        logger.error(f"RAG data for document {indexed_document_id} may be orphaned after metadata write failure")

    return rollback_succeeded