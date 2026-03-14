import cProfile
import pstats
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.cli import main

def profile_command(command_args, output_file):
    print(f"Profiling: oac {' '.join(command_args)}")
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        main(command_args)
    except Exception as e:
        print(f"Error during execution: {e}")
        
    pr.disable()
    
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(20) # Top 20 functions
    
    with open(output_file, 'w') as f:
        f.write(s.getvalue())
    print(f"Profile saved to {output_file}")

if __name__ == "__main__":
    import shutil
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "codex"
        # Profile Hydrate
        profile_command(["hydrate", "codex", "examples/hello-capsule", str(dest)], "/tmp/profile_hydrate.txt")
        # Profile Ingest
        profile_command(["ingest", "codex", str(dest), "examples/hello-capsule"], "/tmp/profile_ingest.txt")
