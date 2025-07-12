import pytest
import sqlite3
from utils.db_utils import load_tags, add_or_update_tag

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / 'test.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE tags (address TEXT PRIMARY KEY, label TEXT, type TEXT, notes TEXT)')
    conn.commit()
    conn.close()
    return str(db_path)

def test_add_and_load_tag(monkeypatch, temp_db):
    monkeypatch.setattr('utils.db_utils.DB_PATH', temp_db)
    add_or_update_tag('test_addr', 'Test Label', 'test_type', 'Test notes')
    tags = load_tags()
    assert 'test_addr' in tags
    assert tags['test_addr']['label'] == 'Test Label'

def test_update_tag(monkeypatch, temp_db):
    monkeypatch.setattr('utils.db_utils.DB_PATH', temp_db)
    add_or_update_tag('test_addr', 'Initial Label', 'init_type')
    add_or_update_tag('test_addr', 'Updated Label', 'updated_type', 'Updated notes')
    tags = load_tags()
    assert tags['test_addr']['label'] == 'Updated Label'
    assert tags['test_addr']['notes'] == 'Updated notes'

def test_load_empty(monkeypatch, temp_db):
    monkeypatch.setattr('utils.db_utils.DB_PATH', temp_db)
    tags = load_tags()
    assert tags == {} 