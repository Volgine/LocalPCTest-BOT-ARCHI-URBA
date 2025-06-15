import json
import subprocess
import pytest
from pathlib import Path


def ensure_jsdom():
    """Skip test if jsdom isn't available."""
    check_cmd = ['node', '-e', 'require("jsdom")']
    if subprocess.run(check_cmd, capture_output=True).returncode != 0:
        pytest.skip("jsdom is not installed")


def test_add_message_sanitizes_html():
    ensure_jsdom()
    script = Path(__file__).with_name('node_test.js')
    result = subprocess.run(['node', str(script)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout.strip())
    assert data['hasImg'] is False
    assert '&lt;img' in data['contentHTML']
