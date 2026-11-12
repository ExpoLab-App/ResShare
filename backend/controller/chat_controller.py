from flask import jsonify, request, session

from backend.controller.helpers import (
    get_indexed_file_stats,
    get_root_node,
    login_required,
    route_logger,
)
from backend.services.answer_service import LocalGenerationClient, GenerationError
from backend.rag.retrieval import search
from backend.rag.config import EMBEDDING_MODEL, collection_name
from backend.rag.prompts import ABSTENTION

def register_chat_routes(app, logger):
    @app.route('/chat', methods=['POST'])
    @login_required
    def chat_route():
        try:
            data = request.get_json()

            if not isinstance(data, dict) or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400

            if not isinstance(data['query'], str):
                return jsonify({'error': 'Query must be text'}), 400
            query = data['query'].strip()
            if not query:
                return jsonify({'error': 'Query cannot be empty'}), 400

            username = session['username']

            generation_client = LocalGenerationClient()
            generation_client.select_context(query, [])
            relevant_chunks = generation_client.select_context(query, search(username, query, top_k=5))

            if not relevant_chunks:
                return jsonify({
                    'answer': ABSTENTION,
                    'sources': [],
                    'chunks_found': 0
                }), 200

            answer = generation_client.generate_answer(query, relevant_chunks)

            sources = []
            seen_files = set()
            for chunk in relevant_chunks:
                filename = chunk['chunk']['metadata']['filename']
                if filename not in seen_files:
                    sources.append({
                        'filename': filename,
                        'score': chunk['score']
                    })
                    seen_files.add(filename)

            return jsonify({
                'answer': answer,
                'sources': sources,
                'chunks_found': len(relevant_chunks)
            }), 200

        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except GenerationError:
            return jsonify({'error': 'Local model could not complete the answer'}), 502
        except RuntimeError:
            return jsonify({'error': 'Document retrieval is temporarily unavailable'}), 503
        except Exception as e:
            route_logger.error(f"Chat endpoint error: {e}")
            return jsonify({'error': 'An error occurred while processing your question'}), 500

    @app.route('/chat/stats', methods=['GET'])
    @login_required
    def chat_stats_route():
        try:
            username = session['username']
            root = get_root_node(username)
            stats = get_indexed_file_stats(root, EMBEDDING_MODEL, collection_name()) if root else {
                'total_chunks': 0,
                'total_files': 0,
                'files': [],
            }

            return jsonify(stats), 200

        except Exception as e:
            route_logger.error(f"Chat stats error: {e}")
            return jsonify({'error': 'Failed to get chat statistics'}), 500
