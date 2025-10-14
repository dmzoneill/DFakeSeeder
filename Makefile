# ============================================================================
# DFakeSeeder Makefile
# ============================================================================
# Comprehensive build and development workflow automation
# See CLAUDE.md for usage documentation

# Package version variables
deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat dfakeseeder.spec | grep Name | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

# ============================================================================
# PHONY Targets Declaration
# ============================================================================
.PHONY: all clean clean-all clean-venv clean_settings clearlog
.PHONY: lint icons ui-build
.PHONY: run run-debug run-debug-venv run-debug-docker
.PHONY: run-tray run-tray-debug run-with-tray run-debug-with-tray
.PHONY: test test-all test-unit test-integration test-fast test-coverage test-parallel test-file test-seed test-venv test-docker
.PHONY: setup-venv required
.PHONY: deb deb-install rpm rpm-install
.PHONY: docker docker-hub docker-ghcr xhosts
.PHONY: flatpak
.PHONY: pypi-build pypi-test-upload pypi-upload pypi-check
.PHONY: translate-build translate-extract translate-clean
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
# Code Quality and Linting
# ============================================================================

clearlog:
	@truncate -s 0 d_fake_seeder/log.log 2>/dev/null || true

lint: clearlog
	@echo "Running lint commands..."
	black -v --line-length=120 .
	flake8 --max-line-length=120
	find . -iname "*.py" -exec isort --profile=black --df {} \;
	@echo "✅ Linting complete!"

# ============================================================================
# UI Building and Icons
# ============================================================================

icons: lint
	@echo "Installing icons..."
	{ \
		for X in 16 32 48 64 96 128 192 256; do \
			mkdir -vp $(HOME)/.icons/hicolor/$${X}x$${X}/apps; \
			mkdir -vp $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps; \
			cp -f $$(pwd)/d_fake_seeder/components/images/dfakeseeder.png $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps/; \
			cp -f $$(pwd)/d_fake_seeder/components/images/dfakeseeder.png $(HOME)/.icons/hicolor/$${X}x$${X}/apps/; \
		done; \
	}
	@echo "Updating icon caches..."
	{ \
		cd $(HOME)/.local/share/icons/ && \
		gtk-update-icon-cache -t -f hicolor; \
		cd $(HOME)/.icons/ && \
		gtk-update-icon-cache -t -f hicolor; \
	}
	@echo "✅ Icons installed!"

ui-build: icons
	@echo "Building UI..."
	xmllint --xinclude d_fake_seeder/components/ui/ui.xml > d_fake_seeder/components/ui/generated/generated.xml
	sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/components/ui/generated/generated.xml
	@echo "✅ UI built successfully!"

# ============================================================================
# Running the Application
# ============================================================================

clean_settings:
	@jq '.torrents = {}' ~/.config/dfakeseeder/settings.json > temp.json && mv temp.json ~/.config/dfakeseeder/settings.json 2>/dev/null || true

run: ui-build
	@echo "Running application..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-rm -rf ~/.cache/gnome-shell/
	-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		cd d_fake_seeder && \
		gtk-launch dfakeseeder; \
	}
	@$(MAKE) clean_settings

run-debug: ui-build
	@echo "Running application with debug output..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-rm -rf ~/.cache/gnome-shell/
	-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder.py; \
	}
	@$(MAKE) clean_settings

run-debug-venv: ui-build
	@echo "Running application with Pipenv and debug output..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-rm -rf ~/.cache/gnome-shell/
	-update-desktop-database ~/.local/share/applications/ 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		pipenv run env LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) python3 d_fake_seeder/dfakeseeder.py; \
	}
	@$(MAKE) clean_settings

run-debug-docker: ui-build
	@echo "Building Docker image..."
	-docker build \
		--build-arg USER_ID=$$(id -u) \
		--build-arg GROUP_ID=$$(id -g) \
		-t dfakeseeder .
	-docker ps -a -q --filter "name=dfakeseeder" | xargs -r docker rm -f
	@echo "Running application in Docker..."
	xhost +local:root
	-docker run --privileged -it --rm \
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
	@$(MAKE) clean_settings

# ============================================================================
# Tray Application Targets
# ============================================================================

run-tray: ui-build
	@echo "Running tray application only..."
	{ \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder_tray.py; \
	}

run-tray-debug: ui-build
	@echo "Running tray application with debug output..."
	{ \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder_tray.py; \
	}

run-with-tray: ui-build
	@echo "Running main application with tray (backgrounded)..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder.py & \
		sleep 3 && \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder_tray.py; \
	}
	@$(MAKE) clean_settings

run-debug-with-tray: ui-build
	@echo "Running main application with tray (debug mode)..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs kill -9 2>/dev/null
	{ \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder.py & \
		sleep 5 && \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd)/d_fake_seeder PYTHONPATH=$$(pwd) /usr/bin/python3 d_fake_seeder/dfakeseeder_tray.py; \
	}
	@$(MAKE) clean_settings

# ============================================================================
# Testing Targets (following TESTING_PLAN.md)
# ============================================================================
# All test targets use Pipenv by default for consistent dependency management

# Run all tests (unit + integration) with Pipenv
test-all:
	@echo "Running all tests with Pipenv..."
	pipenv run pytest tests/ -v
	@echo "✅ All tests complete!"

# Alias for test-all (for convenience)
test: test-all

# Run unit tests only (fast feedback during development)
test-unit:
	@echo "Running unit tests with Pipenv..."
	pipenv run pytest tests/unit -v -m "not slow"
	@echo "✅ Unit tests complete!"

# Run integration tests only
test-integration:
	@echo "Running integration tests with Pipenv..."
	pipenv run pytest tests/integration -v
	@echo "✅ Integration tests complete!"

# Run fast unit tests (excludes slow tests, stops on first failure)
test-fast:
	@echo "Running fast unit tests with Pipenv..."
	pipenv run pytest tests/unit -v -m "not slow" -x
	@echo "✅ Fast tests complete!"

# Run tests with coverage report
test-coverage:
	@echo "Running tests with coverage (Pipenv)..."
	pipenv run pytest tests/ --cov=d_fake_seeder --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated! See htmlcov/index.html"

# Run tests in parallel for speed
test-parallel:
	@echo "Running tests in parallel with Pipenv..."
	pipenv run pytest tests/ -n auto -v
	@echo "✅ Parallel tests complete!"

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
	@echo "Cleaning build artifacts..."
	- sudo rm -rvf log.log
	- sudo rm -rvf d_fake_seeder/log.log
	- sudo rm -rvf dist
	- sudo rm -rvf build
	- sudo rm -rvf *.egg-info
	- sudo rm -rvf .pytest_cache
	- sudo rm -rvf htmlcov
	- sudo rm -rvf .coverage
	- sudo find . -type d -iname __pycache__ -exec rm -rf {} \; 2>/dev/null || true
	- sudo rm -rvf debbuild
	- sudo rm -rvf rpmbuild
	- sudo rm -rvf *.deb
	- sudo rm -rvf *.rpm
	- sudo rm -rvf tools/translations/*.backup
	- sudo rm -rvf tools/translations/*_fallbacks_to_translate.json
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
	@$(MAKE) clean_settings

xprod-wmclass:
	@echo "Getting WM_CLASS property (click on window)..."
	xprop WM_CLASS

# ============================================================================
# Package Building
# ============================================================================

# Build RPM package
rpm: clean
	@echo "Building RPM package..."
	- sudo dnf install -y rpm-build rpmlint python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	cp -r dfakeseeder.spec ./rpmbuild/SPECS/
	cp -r d_fake_seeder/components ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/domain ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/lib ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.py ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.desktop ./rpmbuild/SOURCE/
	tar -czvf rpmbuild/SOURCES/$(RPM_FILENAME).tar.gz d_fake_seeder/
	rpmbuild --define "_topdir `pwd`/rpmbuild" -v -ba ./rpmbuild/SPECS/dfakeseeder.spec
	@echo "✅ RPM package built: $(RPM_FILENAME)"

rpm-install: rpm
	@echo "Installing RPM package..."
	sudo dnf install rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	rpmlint
	@echo "✅ RPM package installed!"

# Build Debian package
deb: clean
	@echo "Building Debian package..."
	sudo apt-get install dpkg dpkg-dev fakeroot
	sudo rm -rvf ./debbuild
	mkdir -vp ./debbuild/DEBIAN
	cp control ./debbuild/DEBIAN
	mkdir -vp ./debbuild/opt/dfakeseeder
	mkdir -vp ./debbuild/usr/share/applications/
	cp -r d_fake_seeder/dfakeseeder.desktop ./debbuild/usr/share/applications/
	cp -r d_fake_seeder/config ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/lib ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/locale ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/domain ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/components ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/dfakeseeder.py ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/dfakeseeder_tray.py ./debbuild/opt/dfakeseeder
	sed 's#Exec=env LOG_LEVEL=DEBUG /usr/bin/python3 dfakeseeder.py#Exec=/usr/bin/python3 /opt/dfakeseeder/dfakeseeder.py#g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	sed 's#Path=.*##g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	touch ./debbuild/DEBIAN/postinst
	echo "#!/bin/bash" >> ./debbuild/DEBIAN/postinst
	echo "# Install icons to user directories" >> ./debbuild/DEBIAN/postinst
	echo "for X in 16 32 48 64 96 128 192 256; do " >> ./debbuild/DEBIAN/postinst
	echo "  mkdir -vp \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	echo "  mkdir -vp \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "  cp -f /opt/dfakeseeder/components/images/dfakeseeder.png \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "done " >> ./debbuild/DEBIAN/postinst
	echo "" >> ./debbuild/DEBIAN/postinst
	echo "# Update icon caches" >> ./debbuild/DEBIAN/postinst
	echo "if [ -d \$$HOME/.local/share/icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	echo "  cd \$$HOME/.local/share/icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "fi" >> ./debbuild/DEBIAN/postinst
	echo "if [ -d \$$HOME/.icons/hicolor ]; then" >> ./debbuild/DEBIAN/postinst
	echo "  cd \$$HOME/.icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "fi" >> ./debbuild/DEBIAN/postinst
	echo "" >> ./debbuild/DEBIAN/postinst
	echo "# Update desktop database" >> ./debbuild/DEBIAN/postinst
	echo "update-desktop-database \$$HOME/.local/share/applications/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "" >> ./debbuild/DEBIAN/postinst
	echo "# Clear GNOME Shell cache for immediate recognition" >> ./debbuild/DEBIAN/postinst
	echo "rm -rf \$$HOME/.cache/gnome-shell/ 2>/dev/null || true" >> ./debbuild/DEBIAN/postinst
	echo "" >> ./debbuild/DEBIAN/postinst
	echo "echo 'Desktop integration installed. GNOME users: Press Alt+F2, type r, and press Enter to restart GNOME Shell.'" >> ./debbuild/DEBIAN/postinst
	chmod 755 ./debbuild/DEBIAN/postinst
	sudo chown -R root:root debbuild
	fakeroot dpkg-deb --build debbuild $(DEB_FILENAME)
	dpkg -c $(DEB_FILENAME)
	dpkg -I $(DEB_FILENAME)
	@echo "✅ Debian package built: $(DEB_FILENAME)"

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
	@echo "Building and running Docker container..."
	docker build -t dfakeseeder .
	docker run --rm --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it dfakeseeder

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
	flatpak-builder build-dir ie.fio.dfakeseeder manifest.json
	@echo "✅ Flatpak built!"

# ============================================================================
# PyPI Publishing
# ============================================================================

pypi-build: clean
	@echo "Building PyPI package..."
	python3 setup.py sdist bdist_wheel
	@echo "✅ PyPI package built successfully!"
	@echo "📦 Distribution files in dist/"
	@ls -lh dist/

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

translate-build:
	@echo "Building translations using translation manager..."
	python3 tools/translation_build_manager.py --build
	@echo "✅ Translations built!"

translate-extract:
	@echo "Extracting translatable strings..."
	python3 tools/translation_build_manager.py --extract
	@echo "✅ Strings extracted!"

translate-clean:
	@echo "Cleaning translation files..."
	python3 tools/translation_build_manager.py --clean
	@echo "✅ Translation files cleaned!"

# ============================================================================
# Help Target
# ============================================================================

help:
	@echo "DFakeSeeder Makefile - Available targets:"
	@echo ""
	@echo "Environment Setup:"
	@echo "  setup-venv          - Setup Pipenv virtual environment"
	@echo "  required            - Install dependencies with Pipenv"
	@echo "  clean-venv          - Remove Pipenv environment"
	@echo ""
	@echo "Development:"
	@echo "  run                 - Run application (production)"
	@echo "  run-debug           - Run with debug output"
	@echo "  run-debug-venv      - Run with Pipenv and debug output"
	@echo "  run-debug-docker    - Run in Docker with debug"
	@echo "  lint                - Run code formatters and linters"
	@echo "  ui-build            - Build UI from XML templates"
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
	@echo "Packaging:"
	@echo "  deb                 - Build Debian package"
	@echo "  deb-install         - Build and install Debian package"
	@echo "  rpm                 - Build RPM package"
	@echo "  rpm-install         - Build and install RPM package"
	@echo "  flatpak             - Build Flatpak package"
	@echo "  docker              - Build and run Docker container"
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
