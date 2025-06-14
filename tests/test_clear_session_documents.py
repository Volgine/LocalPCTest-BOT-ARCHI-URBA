import ast
import asyncio
from pathlib import Path
import types


def get_clear_function(collection_stub, http_exception):
    source = Path('backend/main.py').read_text()
    tree = ast.parse(source)
    func_node = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'clear_session_documents')
    mod = ast.Module(body=[func_node], type_ignores=[])
    code = compile(mod, filename='<ast>', mode='exec')
    class DummyApp:
        def delete(self, *a, **k):
            def wrapper(fn):
                return fn
            return wrapper

    namespace = {
        'collection': collection_stub,
        'HTTPException': http_exception,
        'app': DummyApp(),
    }
    exec(code, namespace)
    return namespace['clear_session_documents']


class DummyCollection:
    def __init__(self):
        self.get_called_with = None
        self.deleted_ids = None
        self.get_return = {'ids': []}

    def get(self, where):
        self.get_called_with = where
        return self.get_return

    def delete(self, ids=None):
        self.deleted_ids = ids


class DummyHTTPException(Exception):
    def __init__(self, status_code=None, detail=None):
        self.status_code = status_code
        self.detail = detail


def test_clear_session_documents_deletes_when_ids_found():
    collection = DummyCollection()
    collection.get_return = {'ids': ['id1', 'id2']}
    func = get_clear_function(collection, DummyHTTPException)
    result = asyncio.run(func('sess1'))
    assert collection.get_called_with == {'session_id': 'sess1'}
    assert collection.deleted_ids == ['id1', 'id2']
    assert result['message'].startswith('2 documents supprim')


def test_clear_session_documents_no_ids():
    collection = DummyCollection()
    collection.get_return = {'ids': []}
    func = get_clear_function(collection, DummyHTTPException)
    result = asyncio.run(func('sess2'))
    assert collection.get_called_with == {'session_id': 'sess2'}
    assert collection.deleted_ids is None
    assert 'Aucun document' in result['message']

