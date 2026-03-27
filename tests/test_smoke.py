from pathlib import Path


def test_expected_project_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'app' / 'main.py').exists()
    assert (root / 'app' / 'api' / 'routes' / 'media.py').exists()
    assert (root / 'FRONTEND_INTEGRATION.md').exists()
