import time
from pathlib import Path

import pytest

try:
    import oac_core
except ImportError:
    oac_core = None

from oac.ingest import _expand_patterns as py_expand_patterns
from oac.proposals import _generate_shared_diff as py_generate_shared_diff


@pytest.mark.skipif(oac_core is None, reason="oac_core not installed")
def test_performance_expand_patterns(tmp_path):
    # Create a large number of files to test glob expansion performance
    root = tmp_path / "perf_test"
    root.mkdir()
    num_files = 1000
    for i in range(num_files):
        (root / f"file_{i}.txt").write_text("content")
        (root / f"other_{i}.log").write_text("other content")
        if i % 10 == 0:
            sub = root / f"sub_{i}"
            sub.mkdir()
            (sub / "nested.txt").write_text("nested")

    patterns = ("**/*.txt",)
    
    # Warm up
    oac_core.expand_patterns(str(root), list(patterns))
    
    start_rust = time.perf_counter()
    rust_results = oac_core.expand_patterns(str(root), list(patterns))
    end_rust = time.perf_counter()
    
    start_py = time.perf_counter()
    py_results = [p.relative_to(root).as_posix() for p in py_expand_patterns(root, patterns)]
    end_py = time.perf_counter()
    
    print(f"\nExpand patterns ({num_files} files): Rust={end_rust-start_rust:.4f}s, Py={end_py-start_py:.4f}s")
    
    assert len(rust_results) == len(py_results)
    assert set(rust_results) == set(py_results)


@pytest.mark.skipif(oac_core is None, reason="oac_core not installed")
def test_performance_diff():
    # Test diff performance with a large number of lines
    num_blocks = 1000
    old_text = "line1\nline2\nline3\n" * num_blocks
    new_text = "line1\nlineX\nline3\n" * num_blocks
    
    # Warm up
    oac_core.generate_shared_diff(old_text, new_text)
    
    start_rust = time.perf_counter()
    rust_diff = oac_core.generate_shared_diff(old_text, new_text)
    end_rust = time.perf_counter()
    
    start_py = time.perf_counter()
    py_diff = py_generate_shared_diff(old_text, new_text)
    end_py = time.perf_counter()
    
    print(f"\nGenerate diff ({num_blocks * 3} lines): Rust={end_rust-start_rust:.4f}s, Py={end_py-start_py:.4f}s")
    
    assert rust_diff["additions"] == py_diff.additions
    assert rust_diff["deletions"] == py_diff.deletions
    assert rust_diff["unchanged"] == py_diff.unchanged
    assert rust_diff["total_lines"] == py_diff.total_lines
