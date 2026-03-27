PYTHONPATH_ENV=PYTHONPATH=src

.PHONY: install lint format test schema fixtures validate-example validate-profiles smoke check

install:
	uv pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest -q

schema:
	$(PYTHONPATH_ENV) python scripts/update_schema.py

fixtures:
	$(PYTHONPATH_ENV) python scripts/update_fixtures.py

validate-example:
	$(PYTHONPATH_ENV) python -m oac validate examples/hello-capsule

validate-profiles:
	$(PYTHONPATH_ENV) python -c "from pathlib import Path; import sys; sys.path.insert(0, 'src'); from oac.profile_io import validate_profile; paths=[Path('examples/adapter-profiles/codex.default.yaml'), Path('examples/adapter-profiles/openclaw.default.yaml'), Path('examples/adapter-profiles/claude-code.default.yaml'), Path('examples/adapter-profiles/opencode.default.yaml'), Path('examples/adapter-profiles/gemini.default.yaml'), Path('examples/adapter-profiles/mcp.default.yaml'), Path('examples/adapter-profiles/webmcp.default.yaml'), Path('examples/adapter-profiles/roblox-embodiment.default.yaml')]; [print(f'valid profile: {validate_profile(path).profile_name}') for path in paths]"

smoke:
	$(PYTHONPATH_ENV) python scripts/smoke_all.py --mode all --quiet

check:
	$(PYTHONPATH_ENV) python3 scripts/check_all.py

benchmark:
	$(PYTHONPATH_ENV) python3 scripts/benchmark.py

