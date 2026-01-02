# Lint and Format Code

Run linting and code formatting for DFakeSeeder.

## Quick Command (Recommended)
```bash
make lint
```

## Comprehensive Linting (Docker-based)
```bash
make super-lint
```

## What `make lint` Does
- **Black**: Code formatting (line length 120, Python 3.11+)
- **isort**: Import ordering (profile: black)
- **flake8**: Linting and style checks
- **mypy**: Type checking

## Standard Import Pattern
All files should follow this pattern for GTK4 imports:

```python
# isort: skip_file

# fmt: off
import other_stdlib_imports
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402
from gi.repository import GLib, GObject  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402

# fmt: on
```

**Why `# fmt: off`?** Prevents Black from reordering `gi.require_version()` calls, which must come before GTK imports.

## Common Lint Fixes
- Line too long: Break at 120 characters
- Unused imports: Remove them
- Missing type hints: Add `-> ReturnType` to functions
- Import order: Let isort fix it automatically









