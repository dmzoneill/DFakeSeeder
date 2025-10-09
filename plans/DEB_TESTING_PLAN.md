# DFakeSeeder DEB Package Testing Plan

**Status:** In Progress
**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Parent Plan:** [TESTING_PLAN.md](TESTING_PLAN.md)

## Overview

This document outlines a comprehensive testing strategy for verifying DFakeSeeder DEB packages in isolated Docker environments. The primary goal is to ensure that the published DEB package installs correctly on Debian-based distributions, includes all dependencies, and functions properly for end users.

## Testing Philosophy

### Core Principles

1. **Isolation First**: All tests run in isolated Docker containers to prevent interference with development environment
2. **Fresh Installation**: Each test starts with a clean environment to simulate real user experience
3. **Platform Coverage**: Test on multiple Debian-based distributions that users commonly use
4. **Automated Verification**: Ansible playbooks verify package functionality without manual intervention
5. **Real User Workflows**: Test scenarios mirror actual user installation and usage patterns
6. **Desktop Integration**: Verify desktop integration scripts work correctly after DEB installation

## Test Platform: Docker

### Why Docker?

- **Complete Isolation**: No interference with host system or development packages
- **Reproducibility**: Same environment every time tests run
- **Multi-Platform**: Easy to test on different Debian-based distributions
- **Fast Cleanup**: Containers can be destroyed and recreated quickly
- **CI/CD Ready**: Docker containers work seamlessly in automated pipelines

### Supported Base Images

Test against Debian-based distributions commonly used by DFakeSeeder users:

1. **Ubuntu 24.04 LTS** (ubuntu:24.04) - Latest LTS
2. **Ubuntu 22.04 LTS** (ubuntu:22.04) - Previous LTS
3. **Debian 12 (Bookworm)** (debian:12) - Stable
4. **Debian 13 (Trixie)** (debian:13) - Testing

## Test Infrastructure

### Docker Test Container

**Dockerfile Template:**

```dockerfile
# DEB package testing with Ansible
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# Install Ansible and DEB tools
RUN apt-get update && apt-get install -y \
    ansible \
    dpkg \
    apt-utils \
    && rm -rf /var/lib/apt/lists/*

# Create test user
RUN useradd -m -s /bin/bash testuser
WORKDIR /home/testuser

# Copy Ansible playbooks
COPY --chown=testuser:testuser ansible/ /home/testuser/ansible/

# Copy DEB package to test
COPY --chown=testuser:testuser *.deb /home/testuser/

USER testuser

# Execute Ansible playbook for DEB verification
CMD ["ansible-playbook", "/home/testuser/ansible/verify_deb_package.yml", "-i", "/home/testuser/ansible/inventory/localhost"]
```

### Ansible Playbook Structure

#### Inventory File

**File:** `tests/deb/ansible/inventory/localhost`

```ini
[test_hosts]
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```

#### DEB Verification Playbook

**File:** `tests/deb/ansible/verify_deb_package.yml`

```yaml
---
- name: DFakeSeeder DEB Package Verification
  hosts: test_hosts
  gather_facts: yes
  become: yes  # DEB installation requires root

  vars:
    deb_package_path: "/home/testuser/d-fake-seeder_*.deb"
    cli_commands:
      - dfs
      - dfakeseeder
      - dfs-install-desktop
      - dfs-uninstall-desktop

  tasks:
    - name: "Stage 1: Install DEB package"
      block:
        - name: Find DEB package file
          find:
            paths: /home/testuser
            patterns: "d-fake-seeder_*.deb"
          register: deb_files

        - name: Install DEB package with apt
          apt:
            deb: "{{ deb_files.files[0].path }}"
            state: present

        - name: Verify package installed
          command: dpkg -l d-fake-seeder
          register: dpkg_query
          changed_when: false
          failed_when: dpkg_query.rc != 0

        - name: Display package info
          debug:
            msg: "✓ DEB package installed successfully"

      rescue:
        - name: DEB installation failed
          fail:
            msg: "Failed to install DEB package"

    - name: "Stage 2: Verify CLI commands"
      become: no  # Run as regular user
      block:
        - name: Check CLI commands exist
          command: "which {{ item }}"
          register: cli_check
          changed_when: false
          failed_when: cli_check.rc != 0
          loop: "{{ cli_commands }}"

        - name: Display CLI locations
          debug:
            msg: "✓ {{ item.item }} found at: {{ item.stdout }}"
          loop: "{{ cli_check.results }}"
          loop_control:
            label: "{{ item.item }}"

      rescue:
        - name: CLI verification failed
          fail:
            msg: "One or more CLI commands not found"

    - name: "Stage 3: Test application launch"
      become: no
      block:
        - name: Run version command
          command: dfs --version
          register: version_output
          changed_when: false
          failed_when: version_output.rc != 0

        - name: Display version
          debug:
            msg: "✓ Version: {{ version_output.stdout }}"

    - name: "Stage 4: Test desktop integration"
      become: no
      block:
        - name: Install desktop integration
          command: dfs-install-desktop
          register: desktop_install
          changed_when: desktop_install.rc == 0

        - name: Verify desktop file
          stat:
            path: "{{ ansible_env.HOME }}/.local/share/applications/dfakeseeder.desktop"
          register: desktop_stat
          failed_when: not desktop_stat.stat.exists

        - name: Uninstall desktop integration
          command: dfs-uninstall-desktop
          register: desktop_uninstall
          changed_when: desktop_uninstall.rc == 0

    - name: "Stage 5: Uninstall DEB package"
      block:
        - name: Remove DEB package
          apt:
            name: d-fake-seeder
            state: absent
            purge: yes

        - name: Verify package removed
          command: dpkg -l d-fake-seeder
          register: dpkg_removed
          changed_when: false
          failed_when: dpkg_removed.rc == 0

        - name: Display uninstall status
          debug:
            msg: "✓ DEB package uninstalled successfully"

      rescue:
        - name: Uninstall failed
          fail:
            msg: "Failed to uninstall DEB package"

    - name: "Final Summary"
      debug:
        msg:
          - "========================================="
          - "  DEB Package Tests Passed!"
          - "========================================="
          - "✓ DEB installation"
          - "✓ CLI commands"
          - "✓ Version check"
          - "✓ Desktop integration"
          - "✓ DEB uninstallation"
          - "========================================="
```

### Ansible Test Orchestration Playbook

**File:** `tests/deb/ansible/run_all_deb_tests.yml`

```yaml
---
- name: Orchestrate DEB Package Tests Across Multiple Platforms
  hosts: localhost
  gather_facts: yes
  become: no

  vars:
    test_platforms:
      - name: ubuntu-24.04
        base_image: ubuntu:24.04
      - name: ubuntu-22.04
        base_image: ubuntu:22.04
      - name: debian-12
        base_image: debian:12
      - name: debian-13
        base_image: debian:13

    test_results_dir: "{{ playbook_dir }}/test_results"
    dockerfile_dir: "{{ playbook_dir }}/../docker"

  tasks:
    - name: Create test results directory
      file:
        path: "{{ test_results_dir }}"
        state: directory
        mode: '0755'

    - name: "Test DEB package on {{ item.name }}"
      block:
        - name: Build Docker test image for {{ item.name }}
          community.docker.docker_image:
            name: "dfakeseeder-deb-test"
            tag: "{{ item.name }}"
            source: build
            build:
              path: "{{ dockerfile_dir }}"
              dockerfile: Dockerfile.deb-test
              args:
                BASE_IMAGE: "{{ item.base_image }}"
            state: present
            force_source: yes
          register: build_result

        - name: Run test container for {{ item.name }}
          community.docker.docker_container:
            name: "dfakeseeder-deb-test-{{ item.name }}"
            image: "dfakeseeder-deb-test:{{ item.name }}"
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
            msg: "✓ Tests passed on {{ item.name }}"

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
              - "  DEB Package Test Summary"
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
            msg: "✓ All DEB package tests passed successfully!"
```

### Ansible Requirements

**File:** `tests/deb/ansible/requirements.yml`

```yaml
---
collections:
  - name: community.docker
    version: ">=3.0.0"
```

Install with:
```bash
ansible-galaxy collection install -r tests/deb/ansible/requirements.yml
```

## Makefile Integration

Add to project Makefile:

```makefile
# DEB Package Testing Targets
.PHONY: test-deb test-deb-ubuntu test-deb-debian test-deb-all

# Test DEB on Ubuntu 24.04
test-deb-ubuntu:
	@echo "Testing DEB package on Ubuntu 24.04..."
	ansible-playbook tests/deb/ansible/run_single_platform.yml \
		-e "platform_name=ubuntu-24.04" \
		-e "base_image=ubuntu:24.04"

# Test DEB on Debian 12
test-deb-debian:
	@echo "Testing DEB package on Debian 12..."
	ansible-playbook tests/deb/ansible/run_single_platform.yml \
		-e "platform_name=debian-12" \
		-e "base_image=debian:12"

# Test DEB on all platforms
test-deb-all:
	@echo "Testing DEB package on all Debian-based distributions..."
	ansible-playbook tests/deb/ansible/run_all_deb_tests.yml

# Quick DEB test (Ubuntu only - default)
test-deb:
	@$(MAKE) test-deb-ubuntu

# View last test results
test-deb-results:
	@echo "=== DEB Test Results Summary ==="
	@find tests/deb/ansible/test_results -name "*.log" -exec echo "{}:" \; -exec head -n 5 {} \; -exec echo "" \;
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deb-package-tests.yml
name: DEB Package Tests

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      package_version:
        description: 'Package version to test (leave empty for latest)'
        required: false

jobs:
  test-deb-installation:
    name: Test on ${{ matrix.platform.name }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        platform:
          - { name: ubuntu-24.04, image: ubuntu:24.04 }
          - { name: ubuntu-22.04, image: ubuntu:22.04 }
          - { name: debian-12, image: debian:12 }
          - { name: debian-13, image: debian:13 }
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

      - name: Run Ansible DEB package tests
        run: |
          ansible-playbook tests/deb/ansible/run_single_platform.yml \
            -e "platform_name=${{ matrix.platform.name }}" \
            -e "base_image=${{ matrix.platform.image }}"

      - name: Upload test logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: deb-test-logs-${{ matrix.platform.name }}
          path: tests/deb/ansible/test_results/
```

## Test Execution

### Local Testing with Ansible

```bash
# Quick smoke test on Ubuntu (uses Ansible)
make test-deb

# Test specific platform (via Ansible playbook)
make test-deb-debian

# Comprehensive test across all platforms (Ansible orchestration)
make test-deb-all

# View test results
make test-deb-results
```

### Manual Ansible Execution

```bash
# Run single platform test directly with Ansible
ansible-playbook tests/deb/ansible/run_single_platform.yml \
    -e "platform_name=ubuntu-24.04" \
    -e "base_image=ubuntu:24.04"

# Run all platforms test
ansible-playbook tests/deb/ansible/run_all_deb_tests.yml

# Run with verbose output for debugging
ansible-playbook tests/deb/ansible/run_single_platform.yml \
    -e "platform_name=ubuntu-24.04" \
    -e "base_image=ubuntu:24.04" \
    -vvv

# Run specific verification playbook inside container manually
docker run --rm -it dfakeseeder-deb-test:ubuntu-24.04 \
    ansible-playbook /home/testuser/ansible/verify_deb_package.yml -i /home/testuser/ansible/inventory/localhost
```

### Manual Docker Testing (Interactive Debugging)

```bash
# Build test container with Ansible
docker build \
    --build-arg BASE_IMAGE=ubuntu:24.04 \
    -f tests/deb/Dockerfile.deb-test \
    -t dfakeseeder-deb-test:ubuntu-24.04 \
    tests/deb/

# Run Ansible playbook in container (automated)
docker run --rm dfakeseeder-deb-test:ubuntu-24.04

# Run interactively for debugging (bash shell)
docker run --rm -it dfakeseeder-deb-test:ubuntu-24.04 /bin/bash

# Inside interactive container, manually run Ansible playbook
# (from within container shell)
ansible-playbook /home/testuser/ansible/verify_deb_package.yml \
    -i /home/testuser/ansible/inventory/localhost
```

### CI/CD Execution

Tests run automatically via Ansible playbooks:
- On every release publication
- Can be triggered manually for specific versions
- Results uploaded to GitHub Actions artifacts
- Ansible provides structured, idempotent test execution
- Test logs saved in `tests/deb/ansible/test_results/`

## Test Maintenance

### Regular Tasks

1. **After Each Release**: Run full DEB test suite via `make test-deb-all`
2. **Weekly**: Spot check latest package on Ubuntu via `make test-deb-ubuntu`
3. **Monthly**: Update Docker base images to latest versions in Ansible playbook variables
4. **Quarterly**: Add new distribution versions to `test_platforms` list in orchestration playbook

### Updating Tests

When adding new features:
1. Update Ansible verification playbook (`verify_deb_package.yml`) with new test stages
2. Add new test tasks for desktop integration changes
3. Update CLI command verification list in playbook variables
4. Update documentation in this plan
5. Test changes with `make test-deb` before committing

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
- **All platforms**: 10-20 minutes
- **CI/CD pipeline**: 15-25 minutes (parallel execution)

### Success Criteria

All tests must pass for release approval:
- ✅ DEB package installs on all supported platforms
- ✅ All dependencies resolved correctly
- ✅ CLI commands work
- ✅ Desktop integration installs and uninstalls cleanly
- ✅ Basic functionality verified
- ✅ Package can be cleanly uninstalled

### Failure Handling

If tests fail:
1. Review test logs in `test_results/`
2. Identify failing test case
3. Fix issue in package or build
4. Rebuild DEB package (increment version)
5. Re-run tests

## Best Practices

### DO:
- ✅ Test in clean containers
- ✅ Use non-root user for testing when possible
- ✅ Verify desktop integration thoroughly
- ✅ Test on multiple Debian-based distributions
- ✅ Check for missing system dependencies
- ✅ Verify CLI scripts are in PATH

### DON'T:
- ❌ Test on host machine (not isolated)
- ❌ Skip platform-specific tests
- ❌ Ignore failed tests
- ❌ Test with development version
- ❌ Run all commands as root
- ❌ Skip desktop integration tests

## Troubleshooting

### Common Issues

**Issue**: Package not found in PATH after installation

**Solution**: Check if `/usr/bin` or `/usr/local/bin` is in PATH, verify DEB installed scripts to correct location

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

## Summary

This DEB testing plan ensures that DFakeSeeder DEB packages work correctly for end users on Debian-based distributions by:

1. **Isolated Testing**: Docker containers prevent interference with development environment
2. **Multi-Platform Verification**: Tests across 4 Debian-based distributions (Ubuntu 24.04, Ubuntu 22.04, Debian 12, Debian 13)
3. **Desktop Integration**: Validates icon installation and desktop file creation
4. **CLI Functionality**: Verifies all command-line scripts work correctly
5. **Ansible Automation**: Structured, idempotent test execution with comprehensive error handling
6. **CI/CD Integration**: Automated testing on every release

### Ansible Advantages

Using Ansible instead of bash scripts provides:

- **Better Structure**: YAML-based declarative syntax instead of imperative bash
- **Reusability**: Modular tasks and blocks can be reused across playbooks
- **Idempotency**: Tasks designed to be run multiple times safely
- **Error Handling**: Block/rescue pattern for comprehensive error recovery
- **Reporting**: Built-in debug output and result aggregation
- **Maintainability**: Easier to read, understand, and modify than bash scripts

**Next Steps:**
1. Create `tests/deb/ansible/` directory structure
2. Implement Dockerfile template with Ansible installation
3. Write Ansible verification playbook (`verify_deb_package.yml`)
4. Write Ansible orchestration playbook (`run_all_deb_tests.yml`)
5. Create Ansible inventory file for localhost testing
6. Add Makefile targets using ansible-playbook commands
7. Set up GitHub Actions workflow with Ansible integration
8. Install ansible-galaxy community.docker collection
9. Run initial test suite on current DEB package with `make test-deb-all`
