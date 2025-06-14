import io
import ast
import types
from pathlib import Path
from docx import Document

def get_extract_function(dummy_doc):
    source = Path('backend/main.py').read_text()
    tree = ast.parse(source)
    func_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'extract_text_from_docx')
    mod = ast.Module(body=[func_node], type_ignores=[])
    code = compile(mod, filename='<ast>', mode='exec')
    namespace = {'docx': types.SimpleNamespace(Document=dummy_doc), 'io': io, 'logger': types.SimpleNamespace(error=lambda *a, **k: None)}
    exec(code, namespace)
    return namespace['extract_text_from_docx']

def test_extract_text_from_docx_uses_bytesio():
    captured = {}
    def dummy_doc(file_obj):
        captured['type'] = type(file_obj)
        class DummyParagraph:
            text = 'hello'
        return types.SimpleNamespace(paragraphs=[DummyParagraph()])
    func = get_extract_function(dummy_doc)
    text = func(b'dummy')
    assert text.strip() == 'hello'
    assert captured['type'] is io.BytesIO


def test_extract_text_from_docx_with_real_bytes():
    buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph("hello world")
    doc.save(buffer)

    func = get_extract_function(Document)
    text = func(buffer.getvalue())
    assert "hello world" in text
