from flask import jsonify, request, session

from backend.controller.helpers import (
    get_indexed_file_stats,
    get_root_node,
    login_required,
    route_logger,
)
from backend.services.answer_service import GeminiGenerationClient
from backend.rag.retrieval import search

def register_chat_routes(app, logger):
    @app.route('/chat', methods=['POST'])
    @login_required
    def chat_route():
        try:
            data = request.get_json()

            if not data or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400

            query = data['query'].strip()
            if not query:
                return jsonify({'error': 'Query cannot be empty'}), 400

            username = session['username']

            relevant_chunks = search(username, query, top_k=5)
            #TODO: Implement reranking and more sophisticated answer generation

            if not relevant_chunks:
                return jsonify({
                    'answer': "I couldn't find any relevant information in your uploaded files to answer this question. Please make sure you have uploaded text-based documents (PDF, DOCX, or TXT files).",
                    'sources': [],
                    'chunks_found': 0
                }), 200

            generation_client = GeminiGenerationClient("gemini-2.5-flash")
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

        except Exception as e:
            route_logger.error(f"Chat endpoint error: {e}")
            return jsonify({'error': 'An error occurred while processing your question'}), 500

    @app.route('/chat/stats', methods=['GET'])
    @login_required
    def chat_stats_route():
        try:
            username = session['username']
            root = get_root_node(username)
            stats = get_indexed_file_stats(root) if root else {
                'total_chunks': 0,
                'total_files': 0,
                'files': [],
            }

            return jsonify(stats), 200

        except Exception as e:
            route_logger.error(f"Chat stats error: {e}")
            return jsonify({'error': 'Failed to get chat statistics'}), 500
