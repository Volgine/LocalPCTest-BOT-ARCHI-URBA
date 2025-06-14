import io
import ast
import types
from pathlib import Path

def get_extract_function(dummy_reader):
    source = Path('backend/main.py').read_text()
    tree = ast.parse(source)
    func_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'extract_text_from_pdf')
    mod = ast.Module(body=[func_node], type_ignores=[])
    code = compile(mod, filename='<ast>', mode='exec')
    namespace = {'PyPDF2': types.SimpleNamespace(PdfReader=dummy_reader), 'io': io, 'logger': types.SimpleNamespace(error=lambda *a, **k: None)}
    exec(code, namespace)
    return namespace['extract_text_from_pdf']

def test_extract_text_from_pdf_uses_bytesio():
    captured = {}
    def dummy_reader(file_obj):
        captured['type'] = type(file_obj)
        class DummyPage:
            def extract_text(self_inner):
                return 'hello'
        return types.SimpleNamespace(pages=[DummyPage()])
    func = get_extract_function(dummy_reader)
    text = func(b'dummy')
    assert text.strip() == 'hello'
    assert captured['type'] is io.BytesIO
