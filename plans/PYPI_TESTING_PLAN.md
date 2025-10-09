# DFakeSeeder PyPI Package Testing Plan

**Status:** In Progress
**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Parent Plan:** [TESTING_PLAN.md](TESTING_PLAN.md)

## Overview

This document outlines a comprehensive testing strategy for verifying DFakeSeeder PyPI packages in isolated environments. The primary goal is to ensure that the published package installs correctly, includes all dependencies, and functions properly for end users across different platforms.

## Testing Philosophy

### Core Principles

1. **Isolation First**: All tests run in isolated Docker containers to prevent interference with development environment
2. **Fresh Installation**: Each test starts with a clean environment to simulate real user experience
3. **Platform Coverage**: Test on multiple Linux distributions that users commonly use
4. **Automated Verification**: Automated scripts verify package functionality without manual intervention
5. **Real User Workflows**: Test scenarios mirror actual user installation and usage patterns
6. **Desktop Integration**: Verify desktop integration scripts work correctly after PyPI installation

## Test Platform: Docker

### Why Docker?

- **Complete Isolation**: No interference with host system or development packages
- **Reproducibility**: Same environment every time tests run
- **Multi-Platform**: Easy to test on different Linux distributions
- **Fast Cleanup**: Containers can be destroyed and recreated quickly
- **CI/CD Ready**: Docker containers work seamlessly in automated pipelines
- **Version Testing**: Can test multiple Python versions simultaneously

### Supported Base Images

Test against distributions commonly used by DFakeSeeder users:

1. **Ubuntu 24.04 LTS** (ubuntu:24.04) - Most popular desktop Linux
2. **Ubuntu 22.04 LTS** (ubuntu:22.04) - Still widely used LTS
3. **Fedora 41** (fedora:41) - Cutting edge packages
4. **Fedora 40** (fedora:40) - Stable release
5. **Debian 12 (Bookworm)** (debian:12) - Stable base
6. **Arch Linux** (archlinux:latest) - Rolling release testing

### Python Versions

Test Python versions supported by DFakeSeeder:

- Python 3.11 (minimum supported)
- Python 3.12 (current stable)
- Python 3.13 (latest)

## Test Categories

### 1. Fresh Installation Tests

**Priority: CRITICAL**

Verify that the package installs from scratch on a clean system.

#### Test 1.1: PyPI Installation - Ubuntu 24.04

**Docker Base:** `ubuntu:24.04`
**Python Version:** 3.12

**Process:**
1. Start fresh Ubuntu 24.04 container
2. Install system dependencies (GTK4, GObject Introspection)
3. Install Python 3.12 and pip
4. Run `pip install d-fake-seeder`
5. Verify installation completes without errors
6. Check installed files in site-packages
7. Verify CLI scripts are in PATH

**Verification:**
- Package installed successfully
- All dependencies resolved
- `dfs` command available
- `dfakeseeder` command available
- `dfs-install-desktop` command available
- `dfs-uninstall-desktop` command available

**Expected Duration:** 2-3 minutes

---

#### Test 1.2: PyPI Installation - Fedora 41

**Docker Base:** `fedora:41`
**Python Version:** 3.13

**Process:**
1. Start fresh Fedora 41 container
2. Install system dependencies (`gtk4`, `python3-gobject`)
3. Run `pip install d-fake-seeder`
4. Verify installation
5. Check CLI scripts

**Verification:**
- Installation succeeds on Fedora
- GTK4 bindings work correctly
- All CLI commands available

**Expected Duration:** 2-3 minutes

---

#### Test 1.3: PyPI Installation - Debian 12

**Docker Base:** `debian:12`
**Python Version:** 3.11

**Process:**
1. Start fresh Debian 12 container
2. Install minimal system dependencies
3. Install with `pip install d-fake-seeder`
4. Verify package and scripts

**Verification:**
- Installation works on Debian
- Minimum Python 3.11 requirement met
- Package functional

**Expected Duration:** 2-3 minutes

---

### 2. Dependency Verification Tests

**Priority: HIGH**

Ensure all required dependencies install correctly.

#### Test 2.1: Python Dependency Resolution

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Fresh container with Python only
2. `pip install d-fake-seeder`
3. Run `pip list` to verify dependencies
4. Check for missing or conflicting packages

**Verification:**
- PyGObject installed and working
- Typer CLI framework available
- bencodepy for torrent parsing
- requests for HTTP communication
- watchdog for file monitoring
- No dependency conflicts
- No missing transitive dependencies

**Expected Duration:** 1-2 minutes

---

#### Test 2.2: System Dependency Check

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install d-fake-seeder in minimal container
2. Run application to detect missing system libraries
3. Document required system packages

**Verification:**
- GTK4 libraries detected
- GObject Introspection available
- Cairo graphics libraries present
- No missing shared libraries

**Expected Duration:** 1-2 minutes

---

### 3. Desktop Integration Tests

**Priority: HIGH**

Verify desktop integration scripts work in isolated environment.

#### Test 3.1: Desktop Integration Installation

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install d-fake-seeder via pip
2. Run `dfs-install-desktop`
3. Verify icon installation
4. Verify desktop file creation
5. Check file permissions

**Verification:**
- Icons installed to `~/.local/share/icons/hicolor/*/apps/dfakeseeder.png`
- Desktop file created at `~/.local/share/applications/dfakeseeder.desktop`
- Desktop file validates with `desktop-file-validate`
- Icons have correct permissions (644)
- Desktop file has correct permissions (644)

**Expected Duration:** 30 seconds

---

#### Test 3.2: Desktop Integration Uninstallation

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install d-fake-seeder and desktop integration
2. Run `dfs-uninstall-desktop`
3. Verify complete cleanup

**Verification:**
- All icons removed from `~/.local/share/icons/`
- Desktop file removed
- No leftover files or directories
- Uninstall script reports success

**Expected Duration:** 30 seconds

---

#### Test 3.3: Icon Cache Update

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install desktop integration
2. Check if icon cache updated
3. Verify icons appear in theme

**Verification:**
- `gtk-update-icon-cache` runs successfully
- Icon theme cache updated
- Icons discoverable by GTK applications

**Expected Duration:** 30 seconds

---

### 4. Functional Smoke Tests

**Priority: MEDIUM**

Verify basic application functionality after PyPI installation.

#### Test 4.1: CLI Launch Test

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install d-fake-seeder via pip
2. Run `dfs --help`
3. Run `dfakeseeder --version`
4. Verify output

**Verification:**
- `dfs` command executes
- `dfakeseeder` command executes
- Help text displays correctly
- Version number shown
- No import errors
- No missing modules

**Expected Duration:** 10 seconds

---

#### Test 4.2: Configuration Initialization

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install package
2. Run `dfs` (launches application)
3. Check for config directory creation
4. Verify default config file

**Verification:**
- `~/.config/dfakeseeder/` directory created
- `settings.json` created from defaults
- `torrents/` subdirectory created
- Default settings valid JSON

**Expected Duration:** 5 seconds

---

#### Test 4.3: Import Test

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install package
2. Run Python import test:
```python
python3 -c "from d_fake_seeder.dfakeseeder import main; print('Import successful')"
```

**Verification:**
- All modules import without errors
- No missing dependencies
- GTK bindings load correctly
- Application entry point accessible

**Expected Duration:** 5 seconds

---

### 5. Upgrade and Downgrade Tests

**Priority: MEDIUM**

Verify package upgrades and downgrades work correctly.

#### Test 5.1: Package Upgrade

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install older version: `pip install d-fake-seeder==0.9.0`
2. Upgrade to latest: `pip install --upgrade d-fake-seeder`
3. Verify upgrade successful
4. Check config migration

**Verification:**
- Upgrade completes without errors
- New version installed
- Old configuration preserved
- Settings migrated correctly
- No file conflicts

**Expected Duration:** 1 minute

---

#### Test 5.2: Package Downgrade

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install latest version
2. Downgrade: `pip install d-fake-seeder==0.9.0`
3. Verify downgrade

**Verification:**
- Downgrade succeeds
- Application still functional
- Config compatibility maintained

**Expected Duration:** 1 minute

---

### 6. Uninstallation Tests

**Priority: MEDIUM**

Verify complete package removal.

#### Test 6.1: Clean Uninstallation

**Docker Base:** `ubuntu:24.04`

**Process:**
1. Install d-fake-seeder
2. Install desktop integration
3. Create some config files
4. Run `dfs-uninstall-desktop`
5. Run `pip uninstall d-fake-seeder`
6. Verify cleanup

**Verification:**
- Package files removed from site-packages
- CLI scripts removed from PATH
- Desktop integration removed
- User config preserved (by design)

**Expected Duration:** 30 seconds

---

### 7. Multi-Python Version Tests

**Priority: MEDIUM**

Verify package works across supported Python versions.

#### Test 7.1: Python 3.11 Compatibility

**Docker Base:** `ubuntu:22.04` (Python 3.11)

**Process:**
1. Install with Python 3.11
2. Run basic functionality tests
3. Verify all features work

**Verification:**
- Installation succeeds
- Application launches
- No version-specific errors

**Expected Duration:** 2 minutes

---

#### Test 7.2: Python 3.12 Compatibility

**Docker Base:** `ubuntu:24.04` (Python 3.12)

**Process:**
1. Install with Python 3.12
2. Test full functionality

**Verification:**
- Works correctly on Python 3.12
- No deprecation warnings

**Expected Duration:** 2 minutes

---

#### Test 7.3: Python 3.13 Compatibility

**Docker Base:** `fedora:41` (Python 3.13)

**Process:**
1. Install with Python 3.13
2. Test cutting-edge compatibility

**Verification:**
- Future-proof package works
- No breaking changes

**Expected Duration:** 2 minutes

---

## Test Infrastructure

### Ansible-Based Test Orchestration

DFakeSeeder uses **Ansible** for test automation instead of bash scripts. This provides better structure, reusability, idempotency, and comprehensive reporting.

### Docker Test Containers

#### Base Dockerfile Template

```dockerfile
# Template for PyPI package testing with Ansible
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# Install Ansible and basic dependencies
RUN apt-get update && apt-get install -y \
    ansible \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-4.0 \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Create test user (don't run as root)
RUN useradd -m -s /bin/bash testuser
WORKDIR /home/testuser

# Copy Ansible playbooks and inventory
COPY --chown=testuser:testuser ansible/ /home/testuser/ansible/

# Run as test user
USER testuser

# Execute Ansible playbook
CMD ["ansible-playbook", "/home/testuser/ansible/verify_pypi_package.yml", "-i", "/home/testuser/ansible/inventory/localhost"]
```

#### Fedora Variant

```dockerfile
FROM fedora:41

# Install Ansible and system dependencies (Fedora)
RUN dnf install -y \
    ansible \
    python3 \
    python3-pip \
    python3-gobject \
    gtk4 \
    && dnf clean all

# Create test user (don't run as root)
RUN useradd -m -s /bin/bash testuser
WORKDIR /home/testuser

# Copy Ansible playbooks and inventory
COPY --chown=testuser:testuser ansible/ /home/testuser/ansible/

# Run as test user
USER testuser

# Execute Ansible playbook
CMD ["ansible-playbook", "/home/testuser/ansible/verify_pypi_package.yml", "-i", "/home/testuser/ansible/inventory/localhost"]
```

### Ansible Playbook Structure

#### Inventory File

**File:** `ansible/inventory/localhost`

```ini
[test_hosts]
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```

#### Main Verification Playbook

**File:** `ansible/verify_pypi_package.yml`

```yaml
---
- name: DFakeSeeder PyPI Package Verification
  hosts: test_hosts
  gather_facts: yes
  become: no  # Run as regular user

  vars:
    package_name: "d-fake-seeder"
    cli_commands:
      - dfs
      - dfakeseeder
      - dfs-install-desktop
      - dfs-uninstall-desktop
    python_modules:
      - d_fake_seeder.dfakeseeder
      - d_fake_seeder.lib.model
      - d_fake_seeder.lib.settings
      - d_fake_seeder.domain.app_settings
    icon_path: "{{ ansible_env.HOME }}/.local/share/icons/hicolor/256x256/apps/dfakeseeder.png"
    desktop_file_path: "{{ ansible_env.HOME }}/.local/share/applications/dfakeseeder.desktop"
    config_dir: "{{ ansible_env.HOME }}/.config/dfakeseeder"

  tasks:
    - name: "Stage 1: Install package from PyPI"
      block:
        - name: Install d-fake-seeder from PyPI
          pip:
            name: "{{ package_name }}"
            state: present
            extra_args: --user

        - name: Verify package installation
          command: "pip3 show {{ package_name }}"
          register: pip_show_result
          changed_when: false
          failed_when: pip_show_result.rc != 0

        - name: Display package info
          debug:
            msg: "Package installed: {{ pip_show_result.stdout_lines[0] }}"

      rescue:
        - name: Installation failed
          fail:
            msg: "Failed to install {{ package_name }} from PyPI"

    - name: "Stage 2: Verify CLI commands exist"
      block:
        - name: Check CLI commands are in PATH
          command: "which {{ item }}"
          register: cli_check
          changed_when: false
          failed_when: cli_check.rc != 0
          loop: "{{ cli_commands }}"

        - name: Display CLI command locations
          debug:
            msg: "✓ {{ item.item }} found at: {{ item.stdout }}"
          loop: "{{ cli_check.results }}"
          loop_control:
            label: "{{ item.item }}"

      rescue:
        - name: CLI commands not found
          fail:
            msg: "One or more CLI commands not found in PATH"

    - name: "Stage 3: Test version command"
      block:
        - name: Run version command
          command: dfs --version
          register: version_output
          changed_when: false
          failed_when: version_output.rc != 0

        - name: Display version
          debug:
            msg: "✓ Version check passed: {{ version_output.stdout }}"

      rescue:
        - name: Version check failed
          fail:
            msg: "Failed to get version information"

    - name: "Stage 4: Test help command"
      block:
        - name: Run help command
          command: dfs --help
          register: help_output
          changed_when: false
          failed_when: help_output.rc != 0

        - name: Verify help text
          assert:
            that:
              - help_output.stdout | length > 0
            success_msg: "✓ Help text displayed successfully"
            fail_msg: "Help text is empty"

      rescue:
        - name: Help command failed
          fail:
            msg: "Failed to display help text"

    - name: "Stage 5: Test Python imports"
      block:
        - name: Test Python module imports
          command: python3 -c "import {{ item }}; print('✓ {{ item }} imported successfully')"
          register: import_results
          changed_when: false
          failed_when: import_results.rc != 0
          loop: "{{ python_modules }}"

        - name: Display import results
          debug:
            msg: "{{ item.stdout }}"
          loop: "{{ import_results.results }}"
          loop_control:
            label: "{{ item.item }}"

      rescue:
        - name: Python imports failed
          fail:
            msg: "Failed to import one or more Python modules"

    - name: "Stage 6: Test desktop integration installation"
      block:
        - name: Run desktop integration install
          command: dfs-install-desktop
          register: desktop_install
          changed_when: desktop_install.rc == 0
          failed_when: desktop_install.rc != 0

        - name: Verify icon file exists
          stat:
            path: "{{ icon_path }}"
          register: icon_stat
          failed_when: not icon_stat.stat.exists

        - name: Verify desktop file exists
          stat:
            path: "{{ desktop_file_path }}"
          register: desktop_stat
          failed_when: not desktop_stat.stat.exists

        - name: Check desktop file permissions
          assert:
            that:
              - desktop_stat.stat.mode == '0644'
            success_msg: "✓ Desktop file has correct permissions"
            fail_msg: "Desktop file permissions incorrect"

        - name: Check icon permissions
          assert:
            that:
              - icon_stat.stat.mode == '0644'
            success_msg: "✓ Icon file has correct permissions"
            fail_msg: "Icon file permissions incorrect"

        - name: Display desktop integration status
          debug:
            msg: "✓ Desktop integration installed successfully"

      rescue:
        - name: Desktop integration install failed
          fail:
            msg: "Failed to install desktop integration"

    - name: "Stage 7: Test desktop integration uninstallation"
      block:
        - name: Run desktop integration uninstall
          command: dfs-uninstall-desktop
          register: desktop_uninstall
          changed_when: desktop_uninstall.rc == 0
          failed_when: desktop_uninstall.rc != 0

        - name: Verify desktop file removed
          stat:
            path: "{{ desktop_file_path }}"
          register: desktop_removed
          failed_when: desktop_removed.stat.exists

        - name: Verify icons removed
          stat:
            path: "{{ icon_path }}"
          register: icon_removed
          failed_when: icon_removed.stat.exists

        - name: Display cleanup status
          debug:
            msg: "✓ Desktop integration cleanup successful"

      rescue:
        - name: Desktop integration cleanup failed
          fail:
            msg: "Failed to uninstall desktop integration"

    - name: "Stage 8: Test configuration initialization"
      block:
        - name: Initialize configuration
          command: |
            python3 -c "
            from d_fake_seeder.domain.app_settings import AppSettings
            settings = AppSettings.get_instance()
            print(f'Config directory: {settings.config_dir}')
            "
          register: config_init
          changed_when: false
          failed_when: config_init.rc != 0

        - name: Verify config directory exists
          stat:
            path: "{{ config_dir }}"
          register: config_stat
          failed_when: not config_stat.stat.exists or not config_stat.stat.isdir

        - name: Display configuration status
          debug:
            msg: "✓ Configuration initialized at {{ config_dir }}"

      rescue:
        - name: Configuration initialization failed
          fail:
            msg: "Failed to initialize configuration"

    - name: "Final Summary"
      debug:
        msg:
          - "========================================="
          - "  All Tests Passed Successfully!"
          - "========================================="
          - "✓ Package installation"
          - "✓ CLI commands"
          - "✓ Version check"
          - "✓ Help text"
          - "✓ Python imports"
          - "✓ Desktop integration install"
          - "✓ Desktop integration cleanup"
          - "✓ Configuration initialization"
          - "========================================="
```

### Ansible Test Orchestration Playbook

**File:** `ansible/run_all_pypi_tests.yml`

```yaml
---
- name: Orchestrate PyPI Package Tests Across Multiple Platforms
  hosts: localhost
  gather_facts: yes
  become: no

  vars:
    test_platforms:
      - name: ubuntu-24.04
        base_image: ubuntu:24.04
        python_version: "3.12"
      - name: ubuntu-22.04
        base_image: ubuntu:22.04
        python_version: "3.11"
      - name: fedora-41
        base_image: fedora:41
        python_version: "3.13"
      - name: fedora-40
        base_image: fedora:40
        python_version: "3.12"
      - name: debian-12
        base_image: debian:12
        python_version: "3.11"

    test_results_dir: "{{ playbook_dir }}/test_results"
    dockerfile_dir: "{{ playbook_dir }}/../docker"

  tasks:
    - name: Create test results directory
      file:
        path: "{{ test_results_dir }}"
        state: directory
        mode: '0755'

    - name: "Test PyPI package on {{ item.name }}"
      block:
        - name: Build Docker test image for {{ item.name }}
          community.docker.docker_image:
            name: "dfakeseeder-pypi-test"
            tag: "{{ item.name }}"
            source: build
            build:
              path: "{{ dockerfile_dir }}"
              dockerfile: Dockerfile.pypi-test
              args:
                BASE_IMAGE: "{{ item.base_image }}"
            state: present
            force_source: yes
          register: build_result

        - name: Run test container for {{ item.name }}
          community.docker.docker_container:
            name: "dfakeseeder-test-{{ item.name }}"
            image: "dfakeseeder-pypi-test:{{ item.name }}"
            state: started
            detach: no
            cleanup: yes
            output_logs: yes
          register: test_result

        - name: Save test output to file
          copy:
            content: "{{ test_result.container.Output }}"
            dest: "{{ test_results_dir }}/{{ item.name }}.test.log"

        - name: Display test result for {{ item.name }}
          debug:
            msg: "✓ Tests passed on {{ item.name }} (Python {{ item.python_version }})"

      rescue:
        - name: Save error output
          copy:
            content: |
              Build Result: {{ build_result | default('N/A') }}
              Test Result: {{ test_result | default('N/A') }}
            dest: "{{ test_results_dir }}/{{ item.name }}.error.log"

        - name: Display test failure for {{ item.name }}
          debug:
            msg: "✗ Tests failed on {{ item.name }} - see {{ test_results_dir }}/{{ item.name }}.error.log"

        - name: Mark platform as failed
          set_fact:
            failed_platforms: "{{ failed_platforms | default([]) + [item.name] }}"

      loop: "{{ test_platforms }}"
      loop_control:
        label: "{{ item.name }}"

    - name: Generate test summary
      block:
        - name: Calculate test statistics
          set_fact:
            total_tests: "{{ test_platforms | length }}"
            failed_count: "{{ failed_platforms | default([]) | length }}"
            passed_count: "{{ test_platforms | length - (failed_platforms | default([]) | length) }}"

        - name: Display test summary
          debug:
            msg:
              - "========================================="
              - "  PyPI Package Test Summary"
              - "========================================="
              - "Total Platforms: {{ total_tests }}"
              - "Passed: {{ passed_count }}"
              - "Failed: {{ failed_count }}"
              - "========================================="
              - "{% if failed_platforms | default([]) | length > 0 %}Failed Platforms: {{ failed_platforms | join(', ') }}{% endif %}"

        - name: Fail if any tests failed
          fail:
            msg: "{{ failed_count }} platform(s) failed testing. Check logs in {{ test_results_dir }}"
          when: failed_count | int > 0

        - name: All tests passed
          debug:
            msg: "✓ All PyPI package tests passed successfully!"
```

### Makefile Integration

Add to project Makefile:

```makefile
# PyPI Package Testing Targets (Ansible-based)
.PHONY: test-pypi test-pypi-ubuntu test-pypi-fedora test-pypi-debian test-pypi-all

# Test PyPI package on Ubuntu 24.04 (single platform via Ansible)
test-pypi-ubuntu:
	@echo "Testing PyPI package on Ubuntu 24.04 via Ansible..."
	ansible-playbook tests/pypi/ansible/run_single_platform.yml \
		-e "platform_name=ubuntu-24.04" \
		-e "base_image=ubuntu:24.04" \
		-e "python_version=3.12"

# Test PyPI package on Fedora 41 (single platform via Ansible)
test-pypi-fedora:
	@echo "Testing PyPI package on Fedora 41 via Ansible..."
	ansible-playbook tests/pypi/ansible/run_single_platform.yml \
		-e "platform_name=fedora-41" \
		-e "base_image=fedora:41" \
		-e "python_version=3.13"

# Test PyPI package on Debian 12 (single platform via Ansible)
test-pypi-debian:
	@echo "Testing PyPI package on Debian 12 via Ansible..."
	ansible-playbook tests/pypi/ansible/run_single_platform.yml \
		-e "platform_name=debian-12" \
		-e "base_image=debian:12" \
		-e "python_version=3.11"

# Run all PyPI package tests (all platforms via Ansible orchestration)
test-pypi-all:
	@echo "Running comprehensive PyPI package tests via Ansible..."
	ansible-playbook tests/pypi/ansible/run_all_pypi_tests.yml

# Quick PyPI smoke test (Ubuntu only - default)
test-pypi:
	@$(MAKE) test-pypi-ubuntu

# View last test results
test-pypi-results:
	@echo "=== Test Results Summary ==="
	@find tests/pypi/ansible/test_results -name "*.log" -exec echo "{}:" \; -exec head -n 5 {} \; -exec echo "" \;
```

### Ansible Requirements

**File:** `ansible/requirements.yml`

```yaml
---
collections:
  - name: community.docker
    version: ">=3.0.0"
```

Install with:
```bash
ansible-galaxy collection install -r tests/pypi/ansible/requirements.yml
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/pypi-package-tests.yml
name: PyPI Package Tests

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      package_version:
        description: 'Package version to test (leave empty for latest)'
        required: false

jobs:
  test-pypi-installation:
    name: Test on ${{ matrix.platform.name }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        platform:
          - { name: ubuntu-24.04, image: ubuntu:24.04, python: "3.12" }
          - { name: ubuntu-22.04, image: ubuntu:22.04, python: "3.11" }
          - { name: fedora-41, image: fedora:41, python: "3.13" }
          - { name: fedora-40, image: fedora:40, python: "3.12" }
          - { name: debian-12, image: debian:12, python: "3.11" }
      fail-fast: false

    steps:
      - uses: actions/checkout@v3

      - name: Install Ansible
        run: |
          sudo apt-get update
          sudo apt-get install -y ansible

      - name: Install Ansible Docker collection
        run: |
          ansible-galaxy collection install community.docker

      - name: Run Ansible PyPI package tests
        run: |
          ansible-playbook tests/pypi/ansible/run_single_platform.yml \
            -e "platform_name=${{ matrix.platform.name }}" \
            -e "base_image=${{ matrix.platform.image }}" \
            -e "python_version=${{ matrix.platform.python }}"

      - name: Upload test logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs-${{ matrix.platform.name }}
          path: tests/pypi/ansible/test_results/

  test-python-versions:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
      fail-fast: false

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Ansible
        run: |
          sudo apt-get update
          sudo apt-get install -y ansible

      - name: Run Ansible verification playbook
        run: |
          ansible-playbook tests/pypi/ansible/verify_python_version.yml \
            -e "python_version=${{ matrix.python-version }}" \
            -e "package_name=d-fake-seeder"
```

## Test Execution

### Local Testing with Ansible

```bash
# Quick smoke test on Ubuntu (uses Ansible)
make test-pypi

# Test specific platform (via Ansible playbook)
make test-pypi-fedora

# Comprehensive test across all platforms (Ansible orchestration)
make test-pypi-all

# View test results
make test-pypi-results
```

### Manual Ansible Execution

```bash
# Run single platform test directly with Ansible
ansible-playbook tests/pypi/ansible/run_single_platform.yml \
    -e "platform_name=ubuntu-24.04" \
    -e "base_image=ubuntu:24.04" \
    -e "python_version=3.12"

# Run all platforms test
ansible-playbook tests/pypi/ansible/run_all_pypi_tests.yml

# Run with verbose output for debugging
ansible-playbook tests/pypi/ansible/run_single_platform.yml \
    -e "platform_name=ubuntu-24.04" \
    -e "base_image=ubuntu:24.04" \
    -e "python_version=3.12" \
    -vvv

# Run specific verification playbook inside container manually
docker run --rm -it dfakeseeder-pypi-test:ubuntu-24.04 \
    ansible-playbook /home/testuser/ansible/verify_pypi_package.yml -i /home/testuser/ansible/inventory/localhost
```

### Manual Docker Testing (Interactive Debugging)

```bash
# Build test container with Ansible
docker build \
    --build-arg BASE_IMAGE=ubuntu:24.04 \
    -f tests/pypi/Dockerfile.pypi-test \
    -t dfakeseeder-pypi-test:ubuntu-24.04 \
    tests/pypi/

# Run Ansible playbook in container (automated)
docker run --rm dfakeseeder-pypi-test:ubuntu-24.04

# Run interactively for debugging (bash shell)
docker run --rm -it dfakeseeder-pypi-test:ubuntu-24.04 /bin/bash

# Inside interactive container, manually run Ansible playbook
# (from within container shell)
ansible-playbook /home/testuser/ansible/verify_pypi_package.yml \
    -i /home/testuser/ansible/inventory/localhost
```

### CI/CD Execution

Tests run automatically via Ansible playbooks:
- On every release publication to PyPI
- Can be triggered manually for specific versions
- Results uploaded to GitHub Actions artifacts
- Ansible provides structured, idempotent test execution
- Test logs saved in `tests/pypi/ansible/test_results/`

## Test Maintenance

### Regular Tasks

1. **After Each Release**: Run full PyPI test suite via `make test-pypi-all`
2. **Weekly**: Spot check latest package on Ubuntu via `make test-pypi-ubuntu`
3. **Monthly**: Update Docker base images to latest versions in Ansible playbook variables
4. **Quarterly**: Add new distribution versions to `test_platforms` list in orchestration playbook

### Updating Tests

When adding new features:
1. Update Ansible verification playbook (`verify_pypi_package.yml`) with new test stages
2. Add new test tasks for desktop integration changes
3. Update CLI command verification list in playbook variables
4. Update Python module import list in playbook variables
5. Update documentation in this plan
6. Test changes with `make test-pypi` before committing

### Ansible Playbook Maintenance

**Regular playbook updates:**
- Review and update task blocks for new verification requirements
- Add rescue blocks for new failure scenarios
- Update variables for new CLI commands or modules
- Enhance debug output for better troubleshooting
- Keep community.docker collection updated (`ansible-galaxy collection install --upgrade community.docker`)

## Expected Results

### Test Duration

- **Single platform test**: 2-5 minutes
- **All platforms**: 15-25 minutes
- **CI/CD pipeline**: 20-30 minutes (parallel execution)

### Success Criteria

All tests must pass for release approval:
- ✅ Package installs on all supported platforms
- ✅ All dependencies resolve correctly
- ✅ CLI commands work
- ✅ Desktop integration installs and uninstalls cleanly
- ✅ Basic functionality verified
- ✅ Python version compatibility confirmed

### Failure Handling

If tests fail:
1. Review test logs in `test_results/`
2. Identify failing test case
3. Fix issue in package or build
4. Re-publish package (increment version)
5. Re-run tests

## Best Practices

### DO:
- ✅ Test in clean containers
- ✅ Use non-root user for testing
- ✅ Verify desktop integration thoroughly
- ✅ Test on multiple Python versions
- ✅ Check for missing system dependencies
- ✅ Verify CLI scripts are in PATH

### DON'T:
- ❌ Test on host machine (not isolated)
- ❌ Skip platform-specific tests
- ❌ Ignore failed tests
- ❌ Test with development version
- ❌ Run as root user
- ❌ Skip desktop integration tests

## Troubleshooting

### Common Issues

**Issue**: Package not found in PATH after installation

**Solution**: Check if `~/.local/bin` is in PATH, verify pip installed to user site

---

**Issue**: GTK4 import errors

**Solution**: Verify system dependencies installed (python3-gi, gir1.2-gtk-4.0)

---

**Issue**: Desktop file validation fails

**Solution**: Check desktop file format, verify .desktop file syntax

---

**Issue**: Icons not showing

**Solution**: Run `gtk-update-icon-cache`, check icon file permissions

---

## Native Package Testing

DFakeSeeder also supports native package formats (RPM and Debian) that are tested separately:

- **RPM Package Testing**: See [RPM_TESTING_PLAN.md](RPM_TESTING_PLAN.md) for comprehensive RPM testing on Red Hat-based distributions (Fedora, Rocky Linux, AlmaLinux)
- **DEB Package Testing**: See [DEB_TESTING_PLAN.md](DEB_TESTING_PLAN.md) for comprehensive DEB testing on Debian-based distributions (Ubuntu, Debian)

Both native package testing plans use the same Ansible-based infrastructure as PyPI testing for consistency and maintainability.

---

## Summary

This PyPI testing plan ensures that DFakeSeeder packages published to PyPI work correctly for end users by:

1. **Isolated Testing**: Docker containers prevent interference with development environment
2. **Multi-Platform Verification**: Tests across 6 Linux distributions (Ubuntu, Fedora, Debian, Arch)
3. **Python Compatibility**: Confirms support for Python 3.11, 3.12, and 3.13
4. **Desktop Integration**: Validates icon installation and desktop file creation
5. **CLI Functionality**: Verifies all command-line scripts work correctly
6. **Ansible Automation**: Structured, idempotent test execution with comprehensive error handling
7. **CI/CD Integration**: Automated testing on every PyPI release

### Ansible Advantages

Using Ansible instead of bash scripts provides:

- **Better Structure**: YAML-based declarative syntax instead of imperative bash
- **Reusability**: Modular tasks and blocks can be reused across playbooks
- **Idempotency**: Tasks designed to be run multiple times safely
- **Error Handling**: Block/rescue pattern for comprehensive error recovery
- **Reporting**: Built-in debug output and result aggregation
- **Maintainability**: Easier to read, understand, and modify than bash scripts

**Next Steps:**
1. Create `tests/pypi/ansible/` directory structure
2. Implement Dockerfile templates with Ansible installation
3. Write Ansible verification playbooks (`verify_pypi_package.yml`, `run_all_pypi_tests.yml`)
4. Create Ansible inventory file for localhost testing
5. Add Makefile targets using ansible-playbook commands
6. Set up GitHub Actions workflow with Ansible integration
7. Install ansible-galaxy community.docker collection
8. Run initial test suite on current package with `make test-pypi-all`

For native package testing (RPM and DEB), refer to the separate testing plans:
- [RPM_TESTING_PLAN.md](RPM_TESTING_PLAN.md)
- [DEB_TESTING_PLAN.md](DEB_TESTING_PLAN.md)
