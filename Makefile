# ============================================================================
# DFakeSeeder Makefile
# ============================================================================
# Comprehensive build and development workflow automation
# See CLAUDE.md for usage documentation

# Package version variables
deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat dfakeseeder.spec | grep "^Name:" | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

# ============================================================================
# PHONY Targets Declaration
# ============================================================================
.PHONY: all clean clean-all clean-venv clean_settings clearlog
.PHONY: lint validate-handlers icons ui-build ui-build-fast
.PHONY: run run-debug run-debug-venv run-debug-docker
.PHONY: run-tray run-tray-debug run-with-tray run-debug-with-tray
.PHONY: test test-all test-unit test-integration test-fast test-coverage test-parallel test-file test-seed test-venv test-docker
.PHONY: setup setup-test setup-venv required
.PHONY: deb deb-quality deb-install rpm rpm-quality rpm-install
.PHONY: docker docker-hub docker-ghcr xhosts
.PHONY: flatpak
.PHONY: pypi-build pypi-test-upload pypi-upload pypi-check
.PHONY: translate-build translate-extract translate-clean translate-check translate-workflow
.PHONY: valgrind xprod-wmclass

# ============================================================================
# Pipenv Environment Management
# ============================================================================
# Note: Uses --system-site-packages to access PyGObject and systemd-python
# These GTK/system libraries cannot be installed via pip

# Setup Pipenv virtual environment with system site packages
setup-venv:
	@echo "Setting up Pipenv virtual environment with system site packages..."
	@echo "This allows access to PyGObject (gi) and other system libraries..."
	PIPENV_PYTHON=/usr/bin/python3 pipenv install --dev --site-packages
	@echo "✅ Pipenv environment ready!"

# Install dependencies with Pipenv
required: setup-venv
	@echo "Installing dependencies with Pipenv..."
	pipenv install --site-packages
	@echo "✅ Dependencies installed!"

# Clean Pipenv environment
clean-venv:
	@echo "Removing Pipenv virtual environment..."
	pipenv --rm || true
	@echo "✅ Pipenv environment removed!"

# ============================================================================
# CI/CD System Setup
# ============================================================================
# Install all system dependencies required for building packages
# This is the main target called by CI/CD pipelines

setup:
	@echo "Installing system dependencies for building packages..."
	@# Detect OS and install required packages
	@if command -v dnf >/dev/null 2>&1; then \
		echo "Detected Fedora/RHEL/CentOS - using dnf..."; \
		sudo dnf install -y \
			rpm-build rpmlint python3-setuptools \
			libxml2 gtk3-devel python3-devel \
			python3-pip python3-black python3-flake8 python3-isort \
			tar findutils sed gawk make pipenv; \
	elif command -v apt-get >/dev/null 2>&1; then \
		echo "Detected Debian/Ubuntu - using apt-get..."; \
		sudo apt-get update && sudo apt-get install -y \
			dpkg dpkg-dev fakeroot \
			libxml2-utils libgtk-3-dev python3-dev \
			python3-pip python3-black python3-flake8 python3-isort \
			make sed coreutils pipenv; \
	elif command -v yum >/dev/null 2>&1; then \
		echo "Detected older RHEL/CentOS - using yum..."; \
		sudo yum install -y \
			rpm-build rpmlint python3-setuptools \
			libxml2 gtk3-devel python3-devel \
			python3-pip tar findutils sed gawk make; \
		sudo pip3 install pipenv black flake8 isort; \
	else \
		echo "❌ ERROR: Unknown package manager. Please install dependencies manually."; \
		echo "Required: rpm-build/dpkg-dev, libxml2-utils, gtk3-devel, python3-dev, black, flake8, isort"; \
		exit 1; \
	fi
	@echo "Installing pipenv if not available..."
	@command -v pipenv >/dev/null 2>&1 || pip3 install --user pipenv
	@echo ""
	@echo "Verifying critical build tools..."
	@command -v xmllint >/dev/null 2>&1 || { echo "❌ ERROR: xmllint not found! Install libxml2 (Fedora/RHEL) or libxml2-utils (Debian/Ubuntu)"; exit 1; }
	@command -v black >/dev/null 2>&1 || { echo "⚠️  WARNING: black not found"; }
	@command -v flake8 >/dev/null 2>&1 || { echo "⚠️  WARNING: flake8 not found"; }
	@command -v isort >/dev/null 2>&1 || { echo "⚠️  WARNING: isort not found"; }
	@echo "✅ Critical tools verified!"
	@echo "✅ System dependencies installed!"
	@$(MAKE) setup-venv

# Setup test environment (installs test-specific dependencies)
test-setup: setup-venv
	@echo "Setting up test environment..."
	pipenv install --dev --site-packages
	@echo "✅ Test environment ready!"

# ============================================================================
# Code Quality and Linting
# ============================================================================

clearlog:
	@truncate -s 0 d_fake_seeder/log.log 2>/dev/null || true

lint: clearlog
	@echo "🔍 Running code quality checks..."
	@echo "   → Running Black formatter..."
	@black . >/dev/null 2>&1 || black .
	@echo "   → Running Flake8 linter..."
	@flake8
	@echo "   → Running isort import checker..."
	@find . -iname "*.py" -exec isort --profile=black --check-only {} \; >/dev/null 2>&1 || true
	@echo "   → Running mypy type checker..."
	@mypy d_fake_seeder
	@echo "✅ Linting complete!"

# Validate settings handler coverage
validate-handlers:
	@echo "Validating settings handler coverage..."
	@python3 tools/validate_settings_handlers.py
	@echo "✅ Validation complete!"

# Validate with debug output
validate-handlers-debug:
	@echo "Validating settings handler coverage (debug mode)..."
	@DFS_DEBUG_HANDLERS=true python3 tools/validate_settings_handlers.py
	@echo "✅ Validation complete!"

# Run GitHub Super-Linter locally
super-lint:
	@echo "Running GitHub Super-Linter..."
	@docker run --rm \
		-e RUN_LOCAL=true \
		-e DEFAULT_BRANCH=main \
		-e VALIDATE_ALL_CODEBASE=true \
		-e VALIDATE_PYTHON_BLACK=true \
		-e VALIDATE_PYTHON_FLAKE8=true \
		-e VALIDATE_PYTHON_ISORT=true \
		-e LINTER_RULES_PATH=. \
		-e VALIDATE_BASH=true \
		-e VALIDATE_BASH_EXEC=true \
		-e VALIDATE_MARKDOWN=true \
		-e VALIDATE_YAML=true \
		-e VALIDATE_XML=true \
		-e PYTHON_BLACK_CONFIG_FILE=pyproject.toml \
		-e PYTHON_FLAKE8_CONFIG_FILE=.flake8 \
		-e PYTHON_ISORT_CONFIG_FILE=.isort.cfg \
		-e MARKDOWN_CONFIG_FILE=.markdownlint.json \
		-e FILTER_REGEX_EXCLUDE=".*/(rpmbuild|debbuild|dist|build|\.venv|\.eggs|__pycache__|\.pytest_cache)/.*" \
		-v $(PWD):/tmp/lint \
		ghcr.io/super-linter/super-linter:latest
	@echo "✅ Super-linter complete!"

# Run Super-Linter with slim image (faster, fewer linters)
super-lint-slim:
	@echo "Running GitHub Super-Linter (slim)..."
	@docker run --rm \
		-e RUN_LOCAL=true \
		-e DEFAULT_BRANCH=main \
		-e VALIDATE_ALL_CODEBASE=true \
		-e VALIDATE_PYTHON_BLACK=true \
		-e VALIDATE_PYTHON_FLAKE8=true \
		-e VALIDATE_PYTHON_ISORT=true \
		-e LINTER_RULES_PATH=. \
		-e VALIDATE_BASH=true \
		-e VALIDATE_MARKDOWN=true \
		-e VALIDATE_YAML=true \
		-e PYTHON_BLACK_CONFIG_FILE=pyproject.toml \
		-e PYTHON_FLAKE8_CONFIG_FILE=.flake8 \
		-e PYTHON_ISORT_CONFIG_FILE=.isort.cfg \
		-e MARKDOWN_CONFIG_FILE=.markdownlint.json \
		-e FILTER_REGEX_EXCLUDE=".*/(rpmbuild|debbuild|dist|build|\.venv|\.eggs|__pycache__|\.pytest_cache)/.*" \
		-v $(PWD):/tmp/lint \
		ghcr.io/super-linter/super-linter:slim-latest
	@echo "✅ Super-linter (slim) complete!"

# ============================================================================
# UI Building and Icons
# ============================================================================

icons: lint
	@echo "🎨 Installing application icons..."
	@echo "   → Installing icon sizes: 16x16 through 256x256..."
	@{ \
		for X in 16 32 48 64 96 128 192 256; do \
			mkdir -p $(HOME)/.icons/hicolor/$${X}x$${X}/apps 2>/dev/null; \
			mkdir -p $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps 2>/dev/null; \
			cp -f $$(pwd)/d_fake_seeder/components/images/dfakeseeder.png $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps/ 2>/dev/null; \
			cp -f $$(pwd)/d_fake_seeder/components/images/dfakeseeder.png $(HOME)/.icons/hicolor/$${X}x$${X}/apps/ 2>/dev/null; \
		done; \
	}
	@echo "   → Updating icon caches..."
	@{ \
		cd $(HOME)/.local/share/icons/ && \
		gtk-update-icon-cache -t -f hicolor 2>/dev/null; \
		cd $(HOME)/.icons/ && \
		gtk-update-icon-cache -t -f hicolor 2>/dev/null; \
	} || true
	@echo "✅ Icons installed!"

ui-build: icons
	@echo "🏗️  Building GTK4 UI..."
	@echo "   → Compiling main UI (ui.xml → generated.xml)..."
	@xmllint --xinclude d_fake_seeder/components/ui/ui.xml > d_fake_seeder/components/ui/generated/generated.xml
	@sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/components/ui/generated/generated.xml
	@echo "   → Compiling settings UI (settings.xml → settings_generated.xml)..."
	@xmllint --xinclude d_fake_seeder/components/ui/settings.xml > d_fake_seeder/components/ui/generated/settings_generated.xml
	@sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/components/ui/generated/settings_generated.xml
	@echo "   → Validating settings UI structure..."
	@python3 tools/validate_settings_xml.py > /dev/null 2>&1 || python3 tools/validate_settings_xml.py
	@echo "✅ UI built successfully!"

# Fast UI build without linting or icon installation (for CI/package builds)
ui-build-fast:
	@echo "Building UI (fast - no linting or icons)..."
	@# Check if generated files exist and are up to date
	@if [ -f d_fake_seeder/components/ui/generated/generated.xml ] && \
	   [ -f d_fake_seeder/components/ui/generated/settings_generated.xml ]; then \
		echo "✅ Generated UI files already exist - skipping UI build"; \
		echo "   (Delete generated/*.xml to force rebuild)"; \
	else \
		echo "Verifying xmllint is available..."; \
		if ! command -v xmllint >/dev/null 2>&1; then \
			echo "❌ xmllint not found - running 'make setup' to install dependencies..."; \
			$(MAKE) setup; \
		fi; \
		echo "Generating UI from XML templates..."; \
		xmllint --xinclude d_fake_seeder/components/ui/ui.xml > d_fake_seeder/components/ui/generated/generated.xml; \
		sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/components/ui/generated/generated.xml; \
		echo "Building settings UI..."; \
		xmllint --xinclude d_fake_seeder/components/ui/settings.xml > d_fake_seeder/components/ui/generated/settings_generated.xml; \
		sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/components/ui/generated/settings_generated.xml; \
		echo "✅ UI built successfully (fast mode)!"; \
	fi

# ============================================================================
# Running the Application
# ============================================================================

clean_settings:
	@jq '.torrents = {}' ~/.config/dfakeseeder/settings.json > temp.json && mv temp.json ~/.config/dfakeseeder/settings.json 2>/dev/null || true

run: ui-build
	@echo "Running application..."
	@-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	@-rm -rf ~/.cache/gnome-shell/ 2>/dev/null
	@-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	@-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs -r kill -9 2>/dev/null || true
	@{ \
		cd d_fake_seeder && \
		gtk-launch dfakeseeder; \
	}
	# @$(MAKE) clean_settings  # DISABLED: Was clearing torrents after every run

run-debug: translate-check ui-build
	@echo "Starting D' Fake Seeder..."
	@-ln -sf $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	@-rm -rf ~/.cache/gnome-shell/ 2>/dev/null
	@-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	@ps aux | grep "[d]fakeseeder.py" | awk '{print $$2}' | xargs -r kill -9 >/dev/null 2>&1 || true
	@PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder.py

run-debug-venv: translate-check ui-build
	@echo "Starting D' Fake Seeder (debug mode)..."
	@-ln -sf $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	@-rm -rf ~/.cache/gnome-shell/ 2>/dev/null
	@-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	@ps aux | grep "[d]fakeseeder.py" | awk '{print $$2}' | xargs -r kill -9 >/dev/null 2>&1 || true
	@PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder.py

run-debug-docker: ui-build
	@echo "Building Docker image..."
	@-docker build \
		--build-arg USER_ID=$$(id -u) \
		--build-arg GROUP_ID=$$(id -g) \
		-t dfakeseeder . 2>&1 | grep -E "(Step|Successfully)" || true
	@-docker ps -a -q --filter "name=dfakeseeder" | xargs -r docker rm -f 2>/dev/null
	@echo "Running application in Docker..."
	@xhost +local:root 2>/dev/null
	@-docker run --privileged -it --rm \
	    --name dfakeseeder \
	    -e LOG_LEVEL=INFO \
	    -e DFS_PATH=/app \
	    -e DISPLAY=$$DISPLAY \
	    -v $$HOME/.config/dfakeseeder:/home/dfakeseeder/.config/dfakeseeder \
		-v $$HOME/Downloads:/home/dfakeseeder/Downloads \
	    -v $$(pwd):/app \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
	    dfakeseeder
	xhost -local:root
	# @$(MAKE) clean_settings  # DISABLED: Was clearing torrents after every run

# ============================================================================
# Tray Application Targets
# ============================================================================

run-tray: ui-build
	@echo "Running tray application with Pipenv..."
	@{ \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder_tray.py; \
	}

run-tray-debug: ui-build
	@echo "Running tray application with Pipenv and debug output..."
	@{ \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder_tray.py; \
	}

run-with-tray: ui-build
	@echo "Running main application with tray (backgrounded) using Pipenv..."
	@-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	@-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs -r kill -9 2>/dev/null || true
	@{ \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder.py & \
		sleep 3 && \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder_tray.py; \
	}
	# @$(MAKE) clean_settings  # DISABLED: Was clearing torrents after every run

run-debug-with-tray: ui-build
	@echo "Running main application with tray (debug mode) using Pipenv..."
	@-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	@-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs -r kill -9 2>/dev/null || true
	@{ \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder.py & \
		sleep 5 && \
		PIPENV_VERBOSITY=-1 pipenv run env LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder_tray.py; \
	}
	# @$(MAKE) clean_settings  # DISABLED: Was clearing torrents after every run

# ============================================================================
# Testing Targets (following TESTING_PLAN.md)
# ============================================================================
# All test targets use Pipenv by default for consistent dependency management

# Run all tests (unit + integration) with Pipenv
test-all:
	@echo "🧪 Running all tests (unit + integration)..."
	@pipenv run pytest tests/ -v
	@echo "✅ All tests passed!"

# Alias for test-all (for convenience)
test: test-all

# Run unit tests only (fast feedback during development)
test-unit:
	@echo "🧪 Running unit tests (excluding slow tests)..."
	@pipenv run pytest tests/unit -v -m "not slow"
	@echo "✅ Unit tests passed!"

# Run integration tests only
test-integration:
	@echo "🧪 Running integration tests..."
	@pipenv run pytest tests/integration -v
	@echo "✅ Integration tests passed!"

# Run fast unit tests (excludes slow tests, stops on first failure)
test-fast:
	@echo "⚡ Running fast unit tests (fail-fast mode)..."
	@pipenv run pytest tests/unit -v -m "not slow" -x
	@echo "✅ Fast tests passed!"

# Run tests with coverage report
test-coverage:
	@echo "📊 Running tests with coverage analysis..."
	@pipenv run pytest tests/ --cov=d_fake_seeder --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated!"
	@echo "   📄 View report: htmlcov/index.html"

# Run tests in parallel for speed
test-parallel:
	@echo "⚡ Running tests in parallel (auto-detected CPUs)..."
	@pipenv run pytest tests/ -n auto -v
	@echo "✅ Parallel tests passed!"

# Run specific test file (usage: make test-file FILE=path/to/test_file.py)
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	@echo "Running test file with Pipenv: $(FILE)"
	pipenv run pytest $(FILE) -v

# Run tests with specific seed for reproducibility (usage: make test-seed SEED=12345)
test-seed:
	@if [ -z "$(SEED)" ]; then \
		echo "Usage: make test-seed SEED=12345"; \
		exit 1; \
	fi
	@echo "Running tests with seed $(SEED) using Pipenv..."
	pipenv run pytest tests/ -v --randomly-seed=$(SEED)

# Run tests with system Python (not recommended - use for CI/CD only)
test-system:
	@echo "⚠️  WARNING: Running tests with system Python (not Pipenv)..."
	@echo "This may fail if dependencies are not installed system-wide."
	pytest tests/ -v
	@echo "✅ System Python tests complete!"

# Run tests in Docker
test-docker:
	@echo "Building Docker test environment..."
	-docker build \
		--build-arg USER_ID=$$(id -u) \
		--build-arg GROUP_ID=$$(id -g) \
		-t dfakeseeder .
	-docker ps -a -q --filter "name=dfakeseeder" | xargs -r docker rm -f
	@echo "Running tests in Docker..."
	-docker run --privileged -it --rm \
	    --name dfakeseeder \
	    -e LOG_LEVEL=INFO \
	    -e DFS_PATH=/app \
	    -e DISPLAY=$$DISPLAY \
		-e PYTHONPATH=/app/d_fake_seeder/ \
	    -v $$HOME/.config/dfakeseeder:/home/dfakeseeder/.config/dfakeseeder \
		-v $$HOME/Downloads:/home/dfakeseeder/Downloads \
	    -v $$(pwd):/app \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
	    dfakeseeder \
	    pytest -s -x -vvv .
	@echo "✅ Docker tests complete!"

# ============================================================================
# Cleanup Targets
# ============================================================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	@echo "   → Removing log files..."
	@sudo rm -rf log.log d_fake_seeder/log.log 2>/dev/null || true
	@echo "   → Removing build directories..."
	@sudo rm -rf dist build *.egg-info .pytest_cache htmlcov .coverage 2>/dev/null || true
	@echo "   → Removing Python cache..."
	@sudo find . -type d -iname __pycache__ -exec rm -rf {} \; 2>/dev/null || true
	@echo "   → Removing package builds..."
	@sudo rm -rf debbuild rpmbuild *.deb *.rpm 2>/dev/null || true
	@echo "   → Removing translation temp files..."
	@sudo rm -rf tools/translations/*.backup tools/translations/*_fallbacks_to_translate.json 2>/dev/null || true
	@echo "✅ Clean complete!"
	@$(MAKE) lint

# Clean everything including Pipenv environment
clean-all: clean clean-venv
	@echo "✅ Complete cleanup finished!"

# ============================================================================
# Debugging and Profiling
# ============================================================================

valgrind: ui-build
	@echo "Running with Valgrind memory checker..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		cd d_fake_seeder && \
		valgrind --tool=memcheck --leak-check=full /usr/bin/python3 dfakeseeder.py; \
	}
	# @$(MAKE) clean_settings  # DISABLED: Was clearing torrents after every run

xprod-wmclass:
	@echo "Getting WM_CLASS property (click on window)..."
	xprop WM_CLASS

# ============================================================================
# Package Building
# ============================================================================

# Build RPM package (fast - for CI, assumes 'make setup' already run)
rpm: ui-build-fast
	@echo "📦 Building RPM package (fast mode)..."
	@echo "   → Cleaning previous build..."
	@rm -rf ./rpmbuild 2>/dev/null || true
	@echo "   → Creating RPM directory structure..."
	@mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	@echo "   → Preparing source files..."
	@mkdir -p ./rpmbuild/$(rpm_package_name)-$(package_version)
	@cp -r d_fake_seeder ./rpmbuild/$(rpm_package_name)-$(package_version)/
	@mkdir -p ./rpmbuild/$(rpm_package_name)-$(package_version)/packaging
	@cp packaging/dfakeseeder-wrapper.sh ./rpmbuild/$(rpm_package_name)-$(package_version)/packaging/
	@cp Pipfile Pipfile.lock ./rpmbuild/$(rpm_package_name)-$(package_version)/
	@echo "   → Creating source tarball..."
	@tar -czf ./rpmbuild/SOURCES/$(rpm_package_name)-$(package_version).tar.gz -C ./rpmbuild $(rpm_package_name)-$(package_version)
	@cp dfakeseeder.spec ./rpmbuild/SPECS/
	@echo "   → Building RPM with rpmbuild..."
	@rpmbuild --define "_topdir $$(pwd)/rpmbuild" -ba ./rpmbuild/SPECS/dfakeseeder.spec 2>&1 | grep -E "(Wrote:|Processing|Executing)" || true
	@echo "✅ RPM package built successfully!"
	@echo ""
	@echo "   → Creating architecture compatibility symlinks..."
	@mkdir -p ./rpmbuild/RPMS/x86_64 2>/dev/null
	@if [ -f ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1.noarch.rpm ]; then \
		cp ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1.noarch.rpm \
		   ./rpmbuild/RPMS/x86_64/$(rpm_package_name)-$(package_version)-1.x86_64.rpm 2>/dev/null; \
	fi
	@echo ""
	@echo "📄 Package locations:"
	@find ./rpmbuild/RPMS -name "*.rpm" -exec echo "   Binary: {}" \; 2>/dev/null
	@find ./rpmbuild/SRPMS -name "*.rpm" -exec echo "   Source: {}" \; 2>/dev/null
	@echo ""
	@echo "📥 Install with:"
	@echo "   sudo dnf install ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1*.rpm"

# Build RPM package with full quality checks (for local development)
rpm-quality: ui-build lint
	@echo "Building RPM package with full quality checks..."
	@echo "Installing RPM build dependencies..."
	- sudo dnf install -y rpm-build rpmlint python3-setuptools 2>/dev/null || sudo yum install -y rpm-build rpmlint python3-setuptools
	@echo "Cleaning previous RPM build..."
	rm -rf ./rpmbuild
	@echo "Creating RPM build directory structure..."
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	@echo "Creating source tarball..."
	mkdir -p ./rpmbuild/$(rpm_package_name)-$(package_version)
	cp -r d_fake_seeder ./rpmbuild/$(rpm_package_name)-$(package_version)/
	mkdir -p ./rpmbuild/$(rpm_package_name)-$(package_version)/packaging
	cp packaging/dfakeseeder-wrapper.sh ./rpmbuild/$(rpm_package_name)-$(package_version)/packaging/
	cp Pipfile ./rpmbuild/$(rpm_package_name)-$(package_version)/
	cp Pipfile.lock ./rpmbuild/$(rpm_package_name)-$(package_version)/
	tar -czf ./rpmbuild/SOURCES/$(rpm_package_name)-$(package_version).tar.gz -C ./rpmbuild $(rpm_package_name)-$(package_version)
	@echo "Copying spec file..."
	cp dfakeseeder.spec ./rpmbuild/SPECS/
	@echo "Building RPM with rpmbuild..."
	rpmbuild --define "_topdir $$(pwd)/rpmbuild" -v -ba ./rpmbuild/SPECS/dfakeseeder.spec
	@echo ""
	@echo "✅ RPM package built successfully with quality checks!"
	@echo ""
	@echo "Creating architecture compatibility symlinks for CI/CD..."
	@mkdir -p ./rpmbuild/RPMS/x86_64
	@if [ -f ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1.noarch.rpm ]; then \
		cp ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1.noarch.rpm \
		   ./rpmbuild/RPMS/x86_64/$(rpm_package_name)-$(package_version)-1.x86_64.rpm; \
		echo "  Created x86_64 copy: ./rpmbuild/RPMS/x86_64/$(rpm_package_name)-$(package_version)-1.x86_64.rpm"; \
	fi
	@echo ""
	@echo "RPM files location:"
	@find ./rpmbuild/RPMS -name "*.rpm" -exec echo "  {}" \;
	@find ./rpmbuild/SRPMS -name "*.rpm" -exec echo "  {}" \;
	@echo ""
	@echo "Install with:"
	@echo "  sudo dnf install ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1*.rpm"
	@echo "  or"
	@echo "  sudo rpm -ivh ./rpmbuild/RPMS/noarch/$(rpm_package_name)-$(package_version)-1*.rpm"
	@echo ""

rpm-install: rpm
	@echo "Installing RPM package..."
	@RPM_FILE=$$(find ./rpmbuild/RPMS/noarch -name "$(rpm_package_name)-$(package_version)-1*.rpm" | head -1); \
	if [ -n "$$RPM_FILE" ]; then \
		echo "Installing: $$RPM_FILE"; \
		sudo dnf install -y "$$RPM_FILE" 2>/dev/null || sudo rpm -ivh "$$RPM_FILE"; \
	else \
		echo "Error: RPM file not found!"; \
		exit 1; \
	fi
	@echo "Running rpmlint on installed package..."
	- rpmlint $(rpm_package_name) 2>/dev/null || echo "rpmlint not available or package has warnings"
	@echo "✅ RPM package installed!"

# Build Debian package (fast - for CI, assumes 'make setup' already run)
deb: ui-build-fast
	@echo "📦 Building Debian package (fast mode)..."
	@echo "   → Cleaning previous build..."
	@sudo rm -rf ./debbuild 2>/dev/null || true
	@echo "   → Creating Debian directory structure..."
	@mkdir -p ./debbuild/DEBIAN
	@cp control ./debbuild/DEBIAN
	@mkdir -p ./debbuild/opt/dfakeseeder ./debbuild/usr/bin ./debbuild/usr/share/applications/
	@echo "   → Copying application files..."
	@cp -r d_fake_seeder/dfakeseeder.desktop ./debbuild/usr/share/applications/
	@cp -r d_fake_seeder/config ./debbuild/opt/dfakeseeder/
	@cp -r d_fake_seeder/lib ./debbuild/opt/dfakeseeder/
	@cp -r d_fake_seeder/domain ./debbuild/opt/dfakeseeder/
	@cp -r d_fake_seeder/components ./debbuild/opt/dfakeseeder/
	@cp d_fake_seeder/*.py ./debbuild/opt/dfakeseeder/
	@echo "   → Installing wrapper script..."
	@cp packaging/dfakeseeder-wrapper.sh ./debbuild/usr/bin/dfakeseeder
	@chmod 755 ./debbuild/usr/bin/dfakeseeder
	@ln -s dfakeseeder ./debbuild/usr/bin/dfs
	@echo "   → Updating desktop file..."
	@sed 's#Exec=env LOG_LEVEL=DEBUG /usr/bin/python3 dfakeseeder.py#Exec=/usr/bin/dfakeseeder#g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	@sed 's#Path=.*##g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	@echo "   → Creating postinst script..."
	@touch ./debbuild/DEBIAN/postinst
	@echo "#!/bin/bash" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Install Python packages not available as DEB packages" >> ./debbuild/DEBIAN/postinst
	@echo "pip3 install --no-cache-dir bencodepy typer==0.12.3 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Install icons to user directories" >> ./debbuild/DEBIAN/postinst
	@echo "for X in 16 32 48 64 96 128 192 256; do " >> ./debbuild/DEBIAN/postinst
	@echo "  mkdir -vp \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	@echo "  mkdir -vp \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	@echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "done " >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Update icon caches" >> ./debbuild/DEBIAN/postinst
	@echo "if [ -d \$$HOME/.local/share/icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	@echo "  cd \$$HOME/.local/share/icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "fi" >> ./debbuild/DEBIAN/postinst
	@echo "if [ -d \$$HOME/.icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	@echo "  cd \$$HOME/.icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "fi" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Update desktop database" >> ./debbuild/DEBIAN/postinst
	@echo "update-desktop-database \$$HOME/.local/share/applications/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Clear GNOME Shell cache for immediate recognition" >> ./debbuild/DEBIAN/postinst
	@echo "rm -rf \$$HOME/.cache/gnome-shell/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "echo 'Desktop integration installed. GNOME users: Press Alt+F2, type r, and press Enter to restart GNOME Shell.'" >> ./debbuild/DEBIAN/postinst
	@chmod 755 ./debbuild/DEBIAN/postinst
	@echo "   → Building package with dpkg-deb..."
	@fakeroot dpkg-deb --build debbuild $(DEB_FILENAME) >/dev/null 2>&1
	@echo "✅ Debian package built successfully!"
	@echo ""
	@echo "📄 Package information:"
	@dpkg -c $(DEB_FILENAME) 2>/dev/null | head -10
	@echo "   ... (showing first 10 files)"
	@echo ""
	@echo "📋 Package details:"
	@dpkg -I $(DEB_FILENAME) 2>/dev/null | grep -E "(Package|Version|Architecture|Description)" || true
	@echo ""
	@echo "📥 Install with:"
	@echo "   sudo dpkg -i $(DEB_FILENAME)"

# Build Debian package with full quality checks (for local development)
deb-quality: clean ui-build lint
	@echo "📦 Building Debian package (with quality checks)..."
	@echo "   → Installing build dependencies..."
	@sudo apt-get install -y dpkg dpkg-dev fakeroot >/dev/null 2>&1
	@echo "   → Cleaning previous build..."
	@sudo rm -rf ./debbuild 2>/dev/null || true
	@echo "   → Creating Debian directory structure..."
	@mkdir -p ./debbuild/DEBIAN
	@cp control ./debbuild/DEBIAN
	@mkdir -p ./debbuild/opt/dfakeseeder ./debbuild/usr/bin ./debbuild/usr/share/applications/
	@echo "   → Copying application files..."
	@cp -r d_fake_seeder/dfakeseeder.desktop ./debbuild/usr/share/applications/
	@cp -r d_fake_seeder/config ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/lib ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/domain ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/components ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/dfakeseeder.py ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/dfakeseeder_tray.py ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/model.py ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/view.py ./debbuild/opt/dfakeseeder
	@cp -r d_fake_seeder/controller.py ./debbuild/opt/dfakeseeder
	@echo "   → Installing wrapper script..."
	@cp packaging/dfakeseeder-wrapper.sh ./debbuild/usr/bin/dfakeseeder
	@chmod 755 ./debbuild/usr/bin/dfakeseeder
	@ln -s dfakeseeder ./debbuild/usr/bin/dfs
	@echo "   → Updating desktop file..."
	@sed 's#Exec=env LOG_LEVEL=DEBUG /usr/bin/python3 dfakeseeder.py#Exec=/usr/bin/dfakeseeder#g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	@sed 's#Path=.*##g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	@echo "   → Creating postinst script..."
	@touch ./debbuild/DEBIAN/postinst
	@echo "#!/bin/bash" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Install Python packages not available as DEB packages" >> ./debbuild/DEBIAN/postinst
	@echo "pip3 install --no-cache-dir bencodepy typer==0.12.3 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Install icons to user directories" >> ./debbuild/DEBIAN/postinst
	@echo "for X in 16 32 48 64 96 128 192 256; do " >> ./debbuild/DEBIAN/postinst
	@echo "  mkdir -vp \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	@echo "  mkdir -vp \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	@echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "done " >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Update icon caches" >> ./debbuild/DEBIAN/postinst
	@echo "if [ -d \$$HOME/.local/share/icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	@echo "  cd \$$HOME/.local/share/icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "fi" >> ./debbuild/DEBIAN/postinst
	@echo "if [ -d \$$HOME/.icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	@echo "  cd \$$HOME/.icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "fi" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Update desktop database" >> ./debbuild/DEBIAN/postinst
	@echo "update-desktop-database \$$HOME/.local/share/applications/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "# Clear GNOME Shell cache for immediate recognition" >> ./debbuild/DEBIAN/postinst
	@echo "rm -rf \$$HOME/.cache/gnome-shell/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	@echo "" >> ./debbuild/DEBIAN/postinst
	@echo "echo 'Desktop integration installed. GNOME users: Press Alt+F2, type r, and press Enter to restart GNOME Shell.'" >> ./debbuild/DEBIAN/postinst
	@chmod 755 ./debbuild/DEBIAN/postinst
	@echo "   → Building package with dpkg-deb..."
	@fakeroot dpkg-deb --build debbuild $(DEB_FILENAME) >/dev/null 2>&1
	@echo "✅ Debian package built successfully!"
	@echo ""
	@echo "📄 Package contents:"
	@dpkg -c $(DEB_FILENAME) 2>/dev/null | head -10
	@echo "   ... (showing first 10 files)"
	@echo ""
	@echo "📋 Package details:"
	@dpkg -I $(DEB_FILENAME) 2>/dev/null | grep -E "(Package|Version|Architecture|Description)" || true
	@echo ""
	@echo "📥 Install with:"
	@echo "   sudo dpkg -i $(DEB_FILENAME)"

deb-install: deb
	@echo "Installing Debian package..."
	sudo dpkg -i $(DEB_FILENAME)
	@echo "✅ Debian package installed!"

# ============================================================================
# Docker Targets
# ============================================================================

xhosts:
	@echo "Allowing local X11 connections..."
	xhost +local:

docker: xhosts
	@echo "🐳 Building and running Docker container..."
	@echo "   → Building image..."
	@docker build -t dfakeseeder . 2>&1 | grep -E "(Step|Successfully)" || true
	@echo "   → Running container..."
	@docker run --rm --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it dfakeseeder

docker-hub: xhosts
	@echo "Running from Docker Hub..."
	docker run --rm --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it feeditout/dfakeseeder

docker-ghcr: xhosts
	@echo "Running from GitHub Container Registry..."
	docker run --rm --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it ghcr.io/dfakeseeder

# ============================================================================
# Flatpak Packaging
# ============================================================================

flatpak: clean
	@echo "Building Flatpak package..."
	flatpak-builder --user --install --force-clean build-dir ie.fio.dfakeseeder.json
	@echo "✅ Flatpak built and installed!"
	@echo "Run with: flatpak run ie.fio.dfakeseeder"

# ============================================================================
# PyPI Publishing
# ============================================================================

pypi-build: clean
	@echo "📦 Building PyPI package..."
	@echo "   → Creating source distribution..."
	@python3 setup.py sdist >/dev/null 2>&1
	@echo "   → Creating wheel distribution..."
	@python3 setup.py bdist_wheel >/dev/null 2>&1
	@echo "✅ PyPI package built successfully!"
	@echo ""
	@echo "📄 Distribution files:"
	@ls -lh dist/ | tail -n +2 | awk '{print "   " $$9 " (" $$5 ")"}'

pypi-test-upload: pypi-build
	@echo "📤 Uploading to TestPyPI..."
	python3 -m twine upload --repository testpypi dist/*
	@echo "✅ Uploaded to TestPyPI: https://test.pypi.org/project/d-fake-seeder/"

pypi-upload: pypi-build
	@echo "⚠️  WARNING: This will upload to production PyPI!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "📤 Uploading to PyPI..."
	python3 -m twine upload dist/*
	@echo "✅ Uploaded to PyPI: https://pypi.org/project/d-fake-seeder/"

pypi-check:
	@echo "🔍 Checking PyPI package..."
	python3 -m twine check dist/*
	@echo "✅ Package check complete!"

# ============================================================================
# Translation Management
# ============================================================================

# Check if translations need updating (compares POT file line count)
translate-check:
	@if [ -f d_fake_seeder/components/locale/dfakeseeder.pot ]; then \
		CURRENT_LINES=$$(wc -l < d_fake_seeder/components/locale/dfakeseeder.pot); \
		if [ -f .pot_linecount ]; then \
			SAVED_LINES=$$(cat .pot_linecount); \
			if [ "$$CURRENT_LINES" != "$$SAVED_LINES" ]; then \
				echo "🔄 POT file changed ($$SAVED_LINES → $$CURRENT_LINES lines) - updating translations..."; \
				$(MAKE) translate-workflow; \
			else \
				echo "✅ Translations up to date ($$CURRENT_LINES translatable strings)"; \
			fi; \
		else \
			echo "$$CURRENT_LINES" > .pot_linecount; \
			echo "📝 Initialized translation tracking ($$CURRENT_LINES strings)"; \
		fi; \
	else \
		echo "⚠️  POT file not found - running initial extraction..."; \
		$(MAKE) translate-workflow; \
	fi

# Full translation workflow: extract → sync → identify fallbacks → validate
translate-workflow:
	@echo "🌐 Running translation workflow (20 languages)..."
	@echo "   → Step 1/7: Extracting strings from Python/XML..."
	@python3 tools/translation_build_manager.py extract > /dev/null 2>&1
	@echo "   → Step 2/7: Syncing to JSON files..."
	@python3 tools/translation_build_manager.py sync > /dev/null 2>&1
	@echo "   → Step 3/7: Syncing keys across languages..."
	@python3 tools/translation_build_manager.py sync-keys > /dev/null 2>&1
	@echo "   → Step 4/7: Identifying fallbacks..."
	@python3 tools/translation_build_manager.py identify-fallbacks > /dev/null 2>&1
	@echo "   → Step 5/7: Creating translation requests..."
	@python3 tools/translation_build_manager.py translate-fallbacks > /dev/null 2>&1
	@echo "   → Step 6/7: Analyzing coverage..."
	@python3 tools/translation_build_manager.py analyze > /dev/null 2>&1
	@echo "   → Step 7/7: Validating translations..."
	@python3 tools/translation_build_manager.py validate > /dev/null 2>&1 || true
	@python3 tools/translation_build_manager.py cleanup > /dev/null 2>&1
	@if [ -f d_fake_seeder/components/locale/dfakeseeder.pot ]; then \
		wc -l < d_fake_seeder/components/locale/dfakeseeder.pot > .pot_linecount; \
	fi
	@echo "✅ Translations updated!"

translate-build:
	@echo "Building translations using translation manager..."
	python3 tools/translation_build_manager.py build
	@echo "✅ Translations built!"

translate-extract:
	@echo "Extracting translatable strings..."
	python3 tools/translation_build_manager.py extract
	@echo "✅ Strings extracted!"

translate-clean:
	@echo "Cleaning translation files..."
	python3 tools/translation_build_manager.py cleanup
	@echo "✅ Translation files cleaned!"

# Audit codebase for untranslated strings
translate-audit:
	@echo "🔍 Auditing codebase for untranslated strings..."
	@python3 tools/translation_build_manager.py audit
	@echo ""

# Audit with JSON output (for CI/automation)
translate-audit-json:
	@python3 tools/translation_build_manager.py audit --json

# Full translation update cycle: extract → sync → build → audit
translate-full:
	@echo "🌐 Running full translation update cycle..."
	@echo ""
	@echo "Step 1/4: Extracting new strings..."
	@python3 tools/translation_build_manager.py extract
	@echo ""
	@echo "Step 2/4: Syncing to JSON files..."
	@python3 tools/translation_build_manager.py sync
	@python3 tools/translation_build_manager.py sync-keys
	@echo ""
	@echo "Step 3/4: Building translation files..."
	@python3 tools/translation_build_manager.py build
	@echo ""
	@echo "Step 4/4: Running translation audit..."
	@python3 tools/translation_audit.py || true
	@echo ""
	@echo "✅ Full translation cycle complete!"

# ============================================================================
# End-to-End Testing
# ============================================================================

# Run full E2E test suite (RPM build, install, launch)
test-e2e:
	@echo "Running end-to-end RPM tests..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	tests/e2e/run_e2e_tests.sh
	@echo "✅ E2E tests complete!"

# Run only installation tests
test-e2e-install:
	@echo "Running RPM installation tests..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	tests/e2e/run_e2e_tests.sh --test install
	@echo "✅ Installation tests complete!"

# Run only launch tests
test-e2e-launch:
	@echo "Running application launch tests..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	tests/e2e/run_e2e_tests.sh --test launch
	@echo "✅ Launch tests complete!"

# Run only uninstall tests
test-e2e-uninstall:
	@echo "Running uninstall tests..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	tests/e2e/run_e2e_tests.sh --test uninstall
	@echo "✅ Uninstall tests complete!"

# Run E2E tests with existing RPM (skip build)
test-e2e-fast:
	@echo "Running E2E tests (skipping build)..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	tests/e2e/run_e2e_tests.sh --skip-build --skip-image
	@echo "✅ Fast E2E tests complete!"

# Build E2E test container image
test-e2e-build-image:
	@echo "Building E2E test container image..."
	cd tests/e2e && podman build -t dfakeseeder-e2e-test:latest -f Dockerfile.fedora .
	@echo "✅ Test image built!"

# Clean E2E test artifacts
clean-e2e:
	@echo "🧹 Cleaning E2E test artifacts..."
	@rm -rf rpmbuild/test-artifacts 2>/dev/null || true
	@echo "✅ E2E artifacts cleaned!"

# ============================================
# PyPI Package E2E Tests
# ============================================

# Run full PyPI E2E test suite (build, install, launch, uninstall)
test-e2e-pypi:
	@echo "Running end-to-end PyPI package tests..."
	@chmod +x tests/e2e/run_pypi_e2e_tests.sh
	tests/e2e/run_pypi_e2e_tests.sh
	@echo "✅ PyPI E2E tests complete!"

# Clean PyPI test artifacts
clean-e2e-pypi:
	@echo "🧹 Cleaning PyPI E2E test artifacts..."
	@rm -rf dist/pypi-e2e-test-report.txt 2>/dev/null || true
	@rm -rf test-artifacts 2>/dev/null || true
	@podman rmi dfakeseeder-e2e-test:latest 2>/dev/null || true
	@echo "✅ PyPI E2E artifacts cleaned!"

# ============================================================================
# DEB Package E2E Tests
# ============================================================================

# Run full DEB E2E test suite (build, install, launch, uninstall)
test-e2e-deb:
	@echo "Running end-to-end DEB package tests..."
	@chmod +x tests/e2e/run_deb_e2e_tests.sh
	tests/e2e/run_deb_e2e_tests.sh
	@echo "✅ DEB E2E tests complete!"

# Run DEB E2E tests on Ubuntu 22.04
test-e2e-deb-ubuntu22:
	@echo "Running DEB E2E tests on Ubuntu 22.04..."
	@chmod +x tests/e2e/run_deb_e2e_tests.sh
	UBUNTU_VERSION=22.04 tests/e2e/run_deb_e2e_tests.sh
	@echo "✅ Ubuntu 22.04 E2E tests complete!"

# Run DEB E2E tests on Ubuntu 24.04
test-e2e-deb-ubuntu24:
	@echo "Running DEB E2E tests on Ubuntu 24.04..."
	@chmod +x tests/e2e/run_deb_e2e_tests.sh
	UBUNTU_VERSION=24.04 tests/e2e/run_deb_e2e_tests.sh
	@echo "✅ Ubuntu 24.04 E2E tests complete!"

# Run DEB E2E tests on Debian 12
test-e2e-deb-debian12:
	@echo "Running DEB E2E tests on Debian 12..."
	@chmod +x tests/e2e/run_deb_e2e_tests.sh
	UBUNTU_VERSION=12 tests/e2e/run_deb_e2e_tests.sh
	@echo "✅ Debian 12 E2E tests complete!"

# Build DEB test container only
build-e2e-deb-image:
	@echo "Building DEB E2E test container..."
	cd tests/e2e && docker build -t dfakeseeder-deb-e2e-test:ubuntu-22.04 -f Dockerfile.ubuntu --build-arg UBUNTU_VERSION=22.04 .
	@echo "✅ DEB E2E test image built!"

# Clean DEB test artifacts
clean-e2e-deb:
	@echo "🧹 Cleaning DEB E2E test artifacts..."
	@rm -rf dist/deb-e2e-test-report.txt 2>/dev/null || true
	@rm -rf dist/debs 2>/dev/null || true
	@rm -rf test-artifacts 2>/dev/null || true
	@docker rmi dfakeseeder-deb-e2e-test:ubuntu-22.04 2>/dev/null || true
	@docker rmi dfakeseeder-deb-e2e-test:ubuntu-24.04 2>/dev/null || true
	@echo "✅ DEB E2E artifacts cleaned!"

# Run all E2E tests (RPM, PyPI, and DEB)
test-e2e-all:
	@echo "🧪 Running all E2E tests..."
	@echo ""
	@echo "📦 1/3: RPM E2E Tests..."
	@$(MAKE) test-e2e
	@echo ""
	@echo "🐍 2/3: PyPI E2E Tests..."
	@$(MAKE) test-e2e-pypi
	@echo ""
	@echo "📦 3/3: DEB E2E Tests..."
	@$(MAKE) test-e2e-deb
	@echo ""
	@echo "✅ All E2E tests complete!"

# ============================================================================
# Help Target
# ============================================================================

help:
	@echo "DFakeSeeder Makefile - Available targets:"
	@echo ""
	@echo "CI/CD Setup:"
	@echo "  setup               - Install all system dependencies for building packages"
	@echo "  test-setup          - Setup test environment (installs test dependencies)"
	@echo ""
	@echo "Environment Setup:"
	@echo "  setup-venv          - Setup Pipenv virtual environment"
	@echo "  required            - Install dependencies with Pipenv"
	@echo "  clean-venv          - Remove Pipenv environment"
	@echo ""
	@echo "Development (all targets use Pipenv by default):"
	@echo "  run                 - Run application (production)"
	@echo "  run-debug           - Run with Pipenv and debug output"
	@echo "  run-debug-venv      - Alias for run-debug"
	@echo "  run-debug-docker    - Run in Docker with debug"
	@echo "  run-tray            - Run tray application with Pipenv"
	@echo "  run-tray-debug      - Run tray application with Pipenv and debug"
	@echo "  run-with-tray       - Run main app with tray using Pipenv"
	@echo "  run-debug-with-tray - Run main app with tray (debug) using Pipenv"
	@echo "  lint                - Run code formatters and linters (black, flake8, isort)"
	@echo "  super-lint          - Run GitHub Super-Linter locally (comprehensive)"
	@echo "  super-lint-slim     - Run Super-Linter slim version (faster)"
	@echo "  ui-build            - Build UI from XML templates (with linting)"
	@echo "  ui-build-fast       - Build UI from XML templates (fast, no linting)"
	@echo "  icons               - Install application icons"
	@echo ""
	@echo "Testing (all targets use Pipenv by default):"
	@echo "  test                - Run all tests (unit + integration)"
	@echo "  test-unit           - Run unit tests only"
	@echo "  test-integration    - Run integration tests only"
	@echo "  test-fast           - Fast unit tests (stop on first failure)"
	@echo "  test-coverage       - Run tests with coverage report"
	@echo "  test-parallel       - Run tests in parallel"
	@echo "  test-file FILE=...  - Run specific test file"
	@echo "  test-seed SEED=...  - Run tests with specific random seed"
	@echo "  test-system         - Run tests with system Python (not recommended)"
	@echo "  test-docker         - Run tests in Docker"
	@echo ""
	@echo "End-to-End Testing (RPM):"
	@echo "  test-e2e            - Run full E2E test suite (build, install, launch)"
	@echo "  test-e2e-install    - Run RPM installation tests only"
	@echo "  test-e2e-launch     - Run application launch tests only"
	@echo "  test-e2e-uninstall  - Run uninstall tests only"
	@echo "  test-e2e-fast       - Run E2E tests with existing RPM (skip build)"
	@echo "  test-e2e-build-image - Build E2E test container image"
	@echo "  clean-e2e           - Clean E2E test artifacts"
	@echo ""
	@echo "End-to-End Testing (PyPI):"
	@echo "  test-e2e-pypi       - Run full PyPI E2E tests (build, install, launch)"
	@echo "  clean-e2e-pypi      - Clean PyPI E2E test artifacts"
	@echo ""
	@echo "Packaging (Fast - for CI/CD, run 'make setup' first):"
	@echo "  deb                 - Build Debian package (fast, no linting)"
	@echo "  deb-install         - Build and install Debian package"
	@echo "  rpm                 - Build RPM package (fast, no linting)"
	@echo "  rpm-install         - Build and install RPM package"
	@echo "  flatpak             - Build Flatpak package"
	@echo "  docker              - Build and run Docker container"
	@echo ""
	@echo "Packaging (Quality - for local development, includes linting):"
	@echo "  deb-quality         - Build Debian package with full quality checks"
	@echo "  rpm-quality         - Build RPM package with full quality checks"
	@echo ""
	@echo "PyPI:"
	@echo "  pypi-build          - Build PyPI distribution"
	@echo "  pypi-test-upload    - Upload to TestPyPI"
	@echo "  pypi-upload         - Upload to production PyPI"
	@echo "  pypi-check          - Check package validity"
	@echo ""
	@echo "Translation:"
	@echo "  translate-build     - Build translation files"
	@echo "  translate-extract   - Extract translatable strings"
	@echo "  translate-clean     - Clean translation files"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean               - Clean build artifacts"
	@echo "  clean-all           - Clean everything including Pipenv"
	@echo ""
	@echo "See CLAUDE.md for detailed documentation"
