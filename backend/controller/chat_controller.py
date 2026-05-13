from flask import jsonify, request, session

from backend.controller.helpers import login_required
from backend.rag_utils import get_llm_integration, get_rag_manager
from backend.controller.helpers import route_logger


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

            rag_manager = get_rag_manager()
            relevant_chunks = rag_manager.search_user_vector_db(username, query, top_k=5)

            if not relevant_chunks:
                return jsonify({
                    'answer': "I couldn't find any relevant information in your uploaded files to answer this question. Please make sure you have uploaded text-based documents (PDF, DOCX, or TXT files).",
                    'sources': [],
                    'chunks_found': 0
                }), 200

            llm_integration = get_llm_integration()
            answer = llm_integration.generate_answer(query, relevant_chunks)

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
            rag_manager = get_rag_manager()
            stats = rag_manager.get_user_stats(username)

            return jsonify(stats), 200

        except Exception as e:
            route_logger.error(f"Chat stats error: {e}")
            return jsonify({'error': 'Failed to get chat statistics'}), 500
