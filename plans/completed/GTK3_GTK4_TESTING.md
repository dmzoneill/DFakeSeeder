# GTK3/GTK4 Testing Strategy

## The Problem

DFakeSeeder uses both GTK4 (main application) and GTK3 (system tray). Due to GObject introspection limitations, **you cannot load both GTK3 and GTK4 in the same Python process**. Once GTK4 is loaded by one test, GTK3 cannot be loaded in subsequent tests.

## The Solution: Process Isolation with pytest-forked

We use **pytest-forked** to run GTK3 tests in separate subprocess, isolating them from GTK4 tests.

### Setup

1. **Install pytest-forked** (already in Pipfile):
   ```bash
   pipenv install --dev pytest-forked
   ```

2. **Mark GTK3 tests** with both markers:
   ```python
   import pytest

   # Apply to entire test file
   pytestmark = [pytest.mark.gtk3, pytest.mark.forked]

   # Or individual tests
   @pytest.mark.gtk3
   @pytest.mark.forked
   def test_tray_something():
       ...
   ```

3. **Mock GTK3 before import** to prevent actual GTK loading:
   ```python
   @pytest.fixture(autouse=True)
   def mock_gtk3_before_import():
       """Mock GTK3 modules before any imports."""
       with patch.dict('sys.modules', {
           'gi': MagicMock(),
           'gi.repository': MagicMock(),
           'gi.repository.AppIndicator3': MagicMock(),
           'gi.repository.Gtk': MagicMock(),  # GTK3, not GTK4
           # ... other GTK3 modules
       }):
           yield
   ```

## Running Tests

### Run All Tests (GTK3 + GTK4)
```bash
# GTK3 tests run in forked subprocess automatically
pipenv run pytest
```text
### Run Only GTK3 Tests
```bash
pipenv run pytest -m gtk3 --forked
```text
### Run Only GTK4 Tests (exclude GTK3)
```bash
pipenv run pytest -m "not gtk3"
```text
### Run Specific GTK3 Test File
```bash
pipenv run pytest tests/unit/test_dfakeseeder_tray_isolated.py --forked
```text
## Example: GTK3 Test File Structure

See `tests/unit/test_dfakeseeder_tray_isolated.py` for a complete example:

```python
"""GTK3 tests that run in isolation."""
import pytest
import sys
from unittest.mock import MagicMock, patch

# Mark ALL tests in this file for forked execution
pytestmark = [pytest.mark.gtk3, pytest.mark.forked]

@pytest.fixture(autouse=True)
def mock_gtk3_before_import():
    """Mock GTK3 to prevent actual loading."""
    # Clean up any existing GTK modules
    gtk_modules = [k for k in sys.modules.keys() if k.startswith('gi.repository.Gtk')]
    for module in gtk_modules:
        sys.modules.pop(module, None)

    # Mock everything
    with patch.dict('sys.modules', {
        'gi': MagicMock(),
        'gi.repository': MagicMock(),
        'gi.repository.AppIndicator3': MagicMock(),
        'gi.repository.Gio': MagicMock(),
        'gi.repository.GLib': MagicMock(),
        'gi.repository.Gtk': MagicMock(),
        'gi.repository.Notify': MagicMock(),
    }):
        yield

def test_tray_functionality():
    """Test tray with mocked GTK3."""
    from d_fake_seeder.dfakeseeder_tray import TrayApplication

    with patch('d_fake_seeder.dfakeseeder_tray.signal.signal'):
        app = TrayApplication()
        assert app.indicator is None
```text
## How It Works

1. **pytest-forked** creates a subprocess for each test marked with `@pytest.mark.forked`
2. The subprocess starts with a **clean Python interpreter** (no GTK4 loaded)
3. GTK3 can be imported/mocked successfully
4. Test runs in isolation
5. Subprocess exits, parent process continues with GTK4 tests

## Benefits

✅ **No GTK3/GTK4 conflicts** - Each runs in separate process
✅ **Comprehensive mocking** - Full control over GTK3 behavior
✅ **Easy to run** - Works seamlessly with normal `pytest` command
✅ **Coverage tracking** - Works with pytest-cov
✅ **Parallel execution** - Compatible with pytest-xdist

## Limitations

⚠️ **Performance overhead** - Forking adds ~50-100ms per test
⚠️ **Memory usage** - Each forked test creates a new process
⚠️ **Shared state** - Cannot share fixtures between forked and non-forked tests

## Best Practices

1. **Keep GTK3 tests minimal** - Only test critical tray functionality
2. **Mock extensively** - Don't rely on actual GTK3 behavior
3. **Use autouse fixtures** - Ensure mocking happens before any imports
4. **Clean sys.modules** - Remove any GTK modules before mocking
5. **Group GTK3 tests** - Keep all GTK3 tests in dedicated files

## Troubleshooting

### "ImportError: cannot import name 'Gtk'" in GTK3 tests
- GTK4 was loaded before GTK3 test ran
- Ensure test has `@pytest.mark.forked` marker
- Check that autouse fixture runs before any imports

### Forked tests don't run
- Install pytest-forked: `pipenv install --dev pytest-forked`
- Add `--forked` flag: `pytest --forked`
- Or use marker: `@pytest.mark.forked`

### Coverage missing for forked tests
- pytest-cov should work automatically
- If not, use: `pytest --cov --forked`

## References

- pytest-forked: <<https://github.com/pytest-dev/pytest-forked>>
- PyGObject: https://pygobject.readthedocs.io/
- GTK3/GTK4 incompatibility: https://discourse.gnome.org/t/using-gtk3-and-gtk4-in-same-process/
