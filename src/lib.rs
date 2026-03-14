use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::exceptions::{PyIOError, PyValueError};
use jwalk::WalkDir;
use globset::{Glob, GlobSetBuilder};
use sha2::{Sha256, Digest};
use std::fs::File;
use std::io::Read;
use std::path::Path;
use similar::{TextDiff, DiffOp};

#[pyfunction]
fn expand_patterns(py: Python<'_>, root: &str, patterns: Vec<&str>) -> PyResult<Vec<String>> {
    let mut builder = GlobSetBuilder::new();
    for p in patterns {
        builder.add(Glob::new(p).map_err(|e| PyValueError::new_err(e.to_string()))?);
    }
    let set = builder.build().map_err(|e| PyValueError::new_err(e.to_string()))?;
    
    let root_path = Path::new(root);
    
    py.allow_threads(|| {
        let mut results = Vec::new();
        // jwalk is parallel by default and handles directory traversal efficiently.
        for entry in WalkDir::new(root).follow_links(false) {
            let entry = entry.map_err(|e| PyIOError::new_err(e.to_string()))?;
            let path = entry.path();
            if path.is_file() {
                // Ensure we correctly handle relative paths by stripping the root prefix.
                let relative_path = path.strip_prefix(root_path).map_err(|e| PyValueError::new_err(e.to_string()))?;
                if let Some(path_str) = relative_path.to_str() {
                    if set.is_match(path_str) {
                        results.push(path_str.to_string());
                    }
                }
            }
        }
        Ok(results)
    })
}

#[pyfunction]
fn hash_file(py: Python<'_>, path: &str) -> PyResult<String> {
    py.allow_threads(|| {
        let mut file = File::open(path).map_err(|e| PyIOError::new_err(e.to_string()))?;
        let mut hasher = Sha256::new();
        let mut buffer = [0; 65536]; // Increased buffer size to 64KB for better cache locality.
        loop {
            let count = file.read(&mut buffer).map_err(|e| PyIOError::new_err(e.to_string()))?;
            if count == 0 { break; }
            hasher.update(&buffer[..count]);
        }
        let hash = hasher.finalize();
        Ok(hex::encode(hash))
    })
}

#[pyfunction]
fn generate_shared_diff(py: Python<'_>, old_text: &str, new_text: &str) -> PyResult<PyObject> {
    let (additions, deletions, unchanged) = py.allow_threads(|| {
        let diff = TextDiff::from_lines(old_text, new_text);
        let mut additions = 0;
        let mut deletions = 0;
        let mut unchanged = 0;
        
        for opcode in diff.opcodes() {
            match opcode {
                DiffOp::Equal { len, .. } => {
                    unchanged += len;
                }
                DiffOp::Insert { len, .. } => {
                    additions += len;
                }
                DiffOp::Delete { len, .. } => {
                    deletions += len;
                }
                DiffOp::Replace { old_len, new_len, .. } => {
                    deletions += old_len;
                    additions += new_len;
                }
            }
        }
        (additions, deletions, unchanged)
    });
    
    let total_lines = additions + deletions + unchanged;
    
    let dict = PyDict::new_bound(py);
    dict.set_item("additions", additions)?;
    dict.set_item("deletions", deletions)?;
    dict.set_item("unchanged", unchanged)?;
    dict.set_item("total_lines", total_lines)?;
    
    Ok(dict.into())
}

#[pymodule]
fn oac_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(expand_patterns, m)?)?;
    m.add_function(wrap_pyfunction!(hash_file, m)?)?;
    m.add_function(wrap_pyfunction!(generate_shared_diff, m)?)?;
    Ok(())
}
