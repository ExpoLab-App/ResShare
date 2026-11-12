import unittest
from unittest.mock import Mock, patch

import numpy as np
import requests
from flask import Flask
from qdrant_client import QdrantClient, models

from backend.controller.chat_controller import register_chat_routes
from backend.controller.helpers import get_indexed_file_stats
from backend.models.file import File
from backend.models.node import Node
from backend.rag.config import EMBEDDING_MODEL, DEFAULT_COLLECTION
from backend.rag.embeddings import LocalEmbeddingClient
from backend.rag.prompts import ABSTENTION, messages
from backend.rag.vector_store import QDrantVectorStore
from backend.services.answer_service import GenerationError, LocalGenerationClient


def chunk(filename='notes.txt', text='The meeting is Tuesday.'):
    return {'chunk': {'text': text, 'metadata': {'filename': filename}}, 'score': 0.9}


class GenerationTests(unittest.TestCase):
    def test_request_uses_shared_prompt_and_bounded_non_thinking_settings(self):
        client = LocalGenerationClient()
        response = Mock()
        response.json.return_value = {'choices': [{'message': {'content': 'Tuesday.'}, 'finish_reason': 'stop'}]}
        with patch('backend.services.answer_service.requests.post', return_value=response) as post:
            self.assertEqual(client.generate_answer('When?', [chunk()]), 'Tuesday.')
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs['json']['messages'], messages('When?', [{'filename': 'notes.txt', 'text': 'The meeting is Tuesday.'}]))
        self.assertEqual(kwargs['json']['max_tokens'], 512)
        self.assertEqual(kwargs['json']['chat_template_kwargs'], {'enable_thinking': False})
        self.assertEqual(kwargs['timeout'], client.timeout)

    def test_no_evidence_needs_no_server(self):
        with patch('backend.services.answer_service.requests.post') as post:
            self.assertEqual(LocalGenerationClient().generate_answer('When?', []), ABSTENTION)
        post.assert_not_called()

    def test_http_timeout_and_malformed_or_truncated_output_fail(self):
        client = LocalGenerationClient()
        for error in (requests.Timeout(), requests.HTTPError()):
            with self.subTest(error=error), patch('backend.services.answer_service.requests.post', side_effect=error):
                with self.assertRaises(GenerationError):
                    client.generate_answer('When?', [chunk()])
        for payload in ({}, {'choices': []}, {'choices': [{'message': {'content': ''}, 'finish_reason': 'stop'}]},
                        {'choices': [{'message': {'content': 'Partial'}, 'finish_reason': 'length'}]},
                        {'choices': [{'message': {'content': '<think>reason</think>Tuesday'}, 'finish_reason': 'stop'}]}):
            with self.subTest(payload=payload), patch('backend.services.answer_service.requests.post') as post:
                post.return_value.json.return_value = payload
                with self.assertRaises(GenerationError):
                    client.generate_answer('When?', [chunk()])

    def test_budget_keeps_whole_chunks_and_rejects_oversized_query(self):
        client = LocalGenerationClient()
        chunks = [chunk('huge.txt', '界' * 6000), chunk()]
        self.assertEqual(client.select_context('When?', chunks), [chunks[1]])
        with self.assertRaises(ValueError):
            client.select_context('界' * 6000, [])


class ChatTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = 'test'
        register_chat_routes(app, None)
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['username'] = 'alice'

    def test_sources_match_only_supplied_evidence_and_user_comes_from_session(self):
        retrieved = [chunk('oversize.txt', 'x' * 7000), chunk('included.txt')]
        with patch('backend.controller.chat_controller.search', return_value=retrieved) as search, patch.object(LocalGenerationClient, 'generate_answer', return_value='Tuesday') as generate:
            response = self.client.post('/chat', json={'query': 'When?', 'username': 'bob'})
        self.assertEqual(response.status_code, 200)
        search.assert_called_once_with('alice', 'When?', top_k=5)
        self.assertEqual(generate.call_args.args[1], [retrieved[1]])
        self.assertEqual(response.json['sources'], [{'filename': 'included.txt', 'score': .9}])
        self.assertEqual(response.json['chunks_found'], 1)

    def test_failures_are_not_successful_abstentions(self):
        with patch('backend.controller.chat_controller.search', side_effect=RuntimeError('offline')):
            self.assertEqual(self.client.post('/chat', json={'query': 'When?'}).status_code, 503)
        with patch('backend.controller.chat_controller.search', return_value=[chunk()]), patch.object(LocalGenerationClient, 'generate_answer', side_effect=GenerationError('offline')):
            self.assertEqual(self.client.post('/chat', json={'query': 'When?'}).status_code, 502)
        for query in (None, [], 3, ''):
            self.assertEqual(self.client.post('/chat', json={'query': query}).status_code, 400)

    def test_no_evidence_abstains_without_generation(self):
        with patch('backend.controller.chat_controller.search', return_value=[]), patch.object(LocalGenerationClient, 'generate_answer') as generate:
            response = self.client.post('/chat', json={'query': 'When?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'answer': ABSTENTION, 'sources': [], 'chunks_found': 0})
        generate.assert_not_called()


class EmbeddingTests(unittest.TestCase):
    def test_passages_queries_and_empty_inputs(self):
        client = LocalEmbeddingClient()
        with patch('backend.rag.embeddings.get_embedding_model') as get_model:
            model = get_model.return_value
            model.passage_embed.return_value = [np.ones(384)]
            model.query_embed.return_value = [np.ones(384)]
            self.assertEqual(client.generate_document_embeddings(['a']).shape, (1, 384))
            self.assertEqual(client.generate_query_embeddings(['b']).shape, (1, 384))
            model.passage_embed.assert_called_once_with(['a'])
            model.query_embed.assert_called_once_with(['b'])
            self.assertEqual(client.generate_document_embeddings([]).shape, (0, 384))
            self.assertEqual(get_model.call_count, 2)

    def test_invalid_embeddings_fail(self):
        for vectors in ([], [np.ones(3)], [np.zeros(384)], [np.full(384, np.nan)], [np.full(384, np.inf)]):
            with self.subTest(vectors=str(vectors)[:30]), patch('backend.rag.embeddings.get_embedding_model') as model:
                model.return_value.passage_embed.return_value = vectors
                with self.assertRaises(ValueError):
                    LocalEmbeddingClient().generate_document_embeddings(['a'])

    def test_wrong_collection_dimension_is_rejected(self):
        db = QdrantClient(':memory:')
        self.addCleanup(db.close)
        db.create_collection(DEFAULT_COLLECTION, vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE))
        with patch('backend.rag.vector_store.QdrantClient', return_value=db):
            store = QDrantVectorStore()
        self.assertFalse(store._ensure_collection())
        with self.assertRaises(RuntimeError):
            store.search_user_vector_db('alice', 'question')
        self.assertEqual(db.get_collection(DEFAULT_COLLECTION).config.params.vectors.size, 768)

    def test_legacy_collection_cannot_be_selected(self):
        from backend.rag.config import collection_name
        with patch.dict('os.environ', {'RAG_COLLECTION': 'resshare_vectors'}):
            with self.assertRaises(ValueError):
                collection_name()

    def test_local_stats_exclude_legacy_metadata(self):
        root = Node('root', True)
        legacy, local = File('old', 1, 'old.txt'), File('new', 1, 'new.txt')
        legacy.mark_rag_ready(5, 'gemini-embedding-001')
        local.mark_rag_ready(2, EMBEDDING_MODEL, DEFAULT_COLLECTION)
        root.add_child(Node('old.txt', False, file_obj=legacy))
        root.add_child(Node('new.txt', False, file_obj=local))
        restored = Node.from_json(root.to_json())
        self.assertEqual(get_indexed_file_stats(restored, EMBEDDING_MODEL, DEFAULT_COLLECTION),
                         {'total_chunks': 2, 'total_files': 1, 'files': ['new.txt']})


if __name__ == '__main__':
    unittest.main()
