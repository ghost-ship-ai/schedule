# Schedule Library Context

## What the project does

Schedule is a Python job scheduling library that provides a simple, human-readable API for running functions periodically. It's designed for in-process scheduling and uses a fluent interface pattern.

Key features:
- Simple API: `schedule.every(10).minutes.do(job_function)`
- Time-based scheduling: seconds, minutes, hours, days, weeks
- Specific time scheduling: `.at("10:30")` 
- Timezone support with pytz
- Tag-based job management
- No external dependencies (pytz is optional)

## Architecture

**Single-file design**: The entire library is contained in `schedule/__init__.py` (945 lines)

**Core classes**:
- `Job`: Represents a scheduled job with timing, function, and metadata
- `Scheduler`: Manages a collection of jobs and runs them
- Module provides a default scheduler instance and convenience functions

**Key patterns**:
- Builder/fluent interface: `every(N).unit.do(function)`
- Decorator support with `@repeat(every().second)`
- UTC offset handling for timezone-aware scheduling

## Key files

- `schedule/__init__.py` - Main library code (945 lines)
- `schedule/py.typed` - Type hints marker file
- `test_schedule.py` - Comprehensive test suite (81 tests)
- `pyproject.toml` - Modern Python packaging
- `setup.py` - Legacy packaging (contains version 1.2.2)
- `requirements-dev.txt` - Development dependencies

## Dependencies

**Runtime**: None (pure Python)
**Optional**: pytz (for timezone support)
**Development**: pytest, pytest-cov, pytest-flake8, black, mypy, sphinx

## Build process

1. `python -m pip install -e .` - Development installation
2. `python -m build` - Creates wheel and source distribution in `dist/`
3. Build outputs: `dist/`, `schedule.egg-info/`, `.pytest_cache`

## Testing status

✅ **Excellent test coverage** - 81 tests all passing
- Comprehensive timezone testing including DST edge cases  
- Error handling and validation testing
- API compatibility testing
- Performance and threading considerations

## Known issues

- Uses older black version (20.8b1) pinned in requirements-dev.txt
- Setup deprecation warnings about license format in pyproject.toml
- Some dependency version conflicts in dev requirements