# DFakeSeeder RPM Package Testing Plan

**Status:** In Progress
**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Parent Plan:** [TESTING_PLAN.md](TESTING_PLAN.md)

## Overview

This document outlines a comprehensive testing strategy for verifying DFakeSeeder RPM packages in isolated Docker environments. The primary goal is to ensure that the published RPM package installs correctly on Red Hat-based distributions, includes all dependencies, and functions properly for end users.

## Testing Philosophy

### Core Principles

1. **Isolation First**: All tests run in isolated Docker containers to prevent interference with development environment
2. **Fresh Installation**: Each test starts with a clean environment to simulate real user experience
3. **Platform Coverage**: Test on multiple Red Hat-based distributions that users commonly use
4. **Automated Verification**: Ansible playbooks verify package functionality without manual intervention
5. **Real User Workflows**: Test scenarios mirror actual user installation and usage patterns
6. **Desktop Integration**: Verify desktop integration scripts work correctly after RPM installation

## Test Platform: Docker

### Why Docker?

- **Complete Isolation**: No interference with host system or development packages
- **Reproducibility**: Same environment every time tests run
- **Multi-Platform**: Easy to test on different Red Hat-based distributions
- **Fast Cleanup**: Containers can be destroyed and recreated quickly
- **CI/CD Ready**: Docker containers work seamlessly in automated pipelines

### Supported Base Images

Test against Red Hat-based distributions commonly used by DFakeSeeder users:

1. **Fedora 41** (fedora:41) - Latest Fedora release
2. **Fedora 40** (fedora:40) - Stable Fedora release
3. **Rocky Linux 9** (rockylinux:9) - RHEL 9 compatible
4. **AlmaLinux 9** (almalinux:9) - RHEL 9 compatible

## Test Infrastructure

### Docker Test Container

**Dockerfile Template:**

```dockerfile
# RPM package testing with Ansible
ARG BASE_IMAGE=fedora:41
FROM ${BASE_IMAGE}

# Install Ansible and RPM tools
RUN dnf install -y \
    ansible \
    rpm \
    dnf-plugins-core \
    && dnf clean all

# Create test user
RUN useradd -m -s /bin/bash testuser
WORKDIR /home/testuser

# Copy Ansible playbooks
COPY --chown=testuser:testuser ansible/ /home/testuser/ansible/

# Copy RPM package to test
COPY --chown=testuser:testuser *.rpm /home/testuser/

USER testuser

# Execute Ansible playbook for RPM verification
CMD ["ansible-playbook", "/home/testuser/ansible/verify_rpm_package.yml", "-i", "/home/testuser/ansible/inventory/localhost"]
```text
### Ansible Playbook Structure

#### Inventory File

**File:** `tests/rpm/ansible/inventory/localhost`

```ini
[test_hosts]
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```text
#### RPM Verification Playbook

**File:** `tests/rpm/ansible/verify_rpm_package.yml`

```yaml
---
- name: DFakeSeeder RPM Package Verification
  hosts: test_hosts
  gather_facts: yes
  become: yes  # RPM installation requires root

  vars:
    rpm_package_path: "/home/testuser/d-fake-seeder-*.rpm"
    cli_commands:
      - dfs
      - dfakeseeder
      - dfs-install-desktop
      - dfs-uninstall-desktop

  tasks:
    - name: "Stage 1: Install RPM package"
      block:
        - name: Find RPM package file
          find:
            paths: /home/testuser
            patterns: "d-fake-seeder-*.rpm"
          register: rpm_files

        - name: Install RPM package with dnf
          dnf:
            name: "{{ rpm_files.files[0].path }}"
            state: present
            disable_gpg_check: yes

        - name: Verify package installed
          command: rpm -q d-fake-seeder
          register: rpm_query
          changed_when: false
          failed_when: rpm_query.rc != 0

        - name: Display package info
          debug:
            msg: "✓ RPM package installed: {{ rpm_query.stdout }}"

      rescue:
        - name: RPM installation failed
          fail:
            msg: "Failed to install RPM package"

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

    - name: "Stage 5: Uninstall RPM package"
      block:
        - name: Remove RPM package
          dnf:
            name: d-fake-seeder
            state: absent

        - name: Verify package removed
          command: rpm -q d-fake-seeder
          register: rpm_removed
          changed_when: false
          failed_when: rpm_removed.rc == 0

        - name: Display uninstall status
          debug:
            msg: "✓ RPM package uninstalled successfully"

      rescue:
        - name: Uninstall failed
          fail:
            msg: "Failed to uninstall RPM package"

    - name: "Final Summary"
      debug:
        msg:
          - "========================================="
          - "  RPM Package Tests Passed!"
          - "========================================="
          - "✓ RPM installation"
          - "✓ CLI commands"
          - "✓ Version check"
          - "✓ Desktop integration"
          - "✓ RPM uninstallation"
          - "========================================="
```text
### Ansible Test Orchestration Playbook

**File:** `tests/rpm/ansible/run_all_rpm_tests.yml`

```yaml
---
- name: Orchestrate RPM Package Tests Across Multiple Platforms
  hosts: localhost
  gather_facts: yes
  become: no

  vars:
    test_platforms:
      - name: fedora-41
        base_image: fedora:41
      - name: fedora-40
        base_image: fedora:40
      - name: rocky-9
        base_image: rockylinux:9
      - name: alma-9
        base_image: almalinux:9

    test_results_dir: "{{ playbook_dir }}/test_results"
    dockerfile_dir: "{{ playbook_dir }}/../docker"

  tasks:
    - name: Create test results directory
      file:
        path: "{{ test_results_dir }}"
        state: directory
        mode: '0755'

    - name: "Test RPM package on {{ item.name }}"
      block:
        - name: Build Docker test image for {{ item.name }}
          community.docker.docker_image:
            name: "dfakeseeder-rpm-test"
            tag: "{{ item.name }}"
            source: build
            build:
              path: "{{ dockerfile_dir }}"
              dockerfile: Dockerfile.rpm-test
              args:
                BASE_IMAGE: "{{ item.base_image }}"
            state: present
            force_source: yes
          register: build_result

        - name: Run test container for {{ item.name }}
          community.docker.docker_container:
            name: "dfakeseeder-rpm-test-{{ item.name }}"
            image: "dfakeseeder-rpm-test:{{ item.name }}"
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
              - "  RPM Package Test Summary"
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
            msg: "✓ All RPM package tests passed successfully!"
```text
### Ansible Requirements

**File:** `tests/rpm/ansible/requirements.yml`

```yaml
---
collections:
  - name: community.docker
    version: ">=3.0.0"
```text
Install with:
```bash
ansible-galaxy collection install -r tests/rpm/ansible/requirements.yml
```text
## Makefile Integration

Add to project Makefile:

```makefile
# RPM Package Testing Targets
.PHONY: test-rpm test-rpm-fedora test-rpm-rocky test-rpm-alma test-rpm-all

# Test RPM on Fedora 41
test-rpm-fedora:
	@echo "Testing RPM package on Fedora 41..."
	ansible-playbook tests/rpm/ansible/run_single_platform.yml \
		-e "platform_name=fedora-41" \
		-e "base_image=fedora:41"

# Test RPM on Rocky Linux 9
test-rpm-rocky:
	@echo "Testing RPM package on Rocky Linux 9..."
	ansible-playbook tests/rpm/ansible/run_single_platform.yml \
		-e "platform_name=rocky-9" \
		-e "base_image=rockylinux:9"

# Test RPM on AlmaLinux 9
test-rpm-alma:
	@echo "Testing RPM package on AlmaLinux 9..."
	ansible-playbook tests/rpm/ansible/run_single_platform.yml \
		-e "platform_name=alma-9" \
		-e "base_image=almalinux:9"

# Test RPM on all platforms
test-rpm-all:
	@echo "Testing RPM package on all Red Hat-based distributions..."
	ansible-playbook tests/rpm/ansible/run_all_rpm_tests.yml

# Quick RPM test (Fedora only - default)
test-rpm:
	@$(MAKE) test-rpm-fedora

# View last test results
test-rpm-results:
	@echo "=== RPM Test Results Summary ==="
	@find tests/rpm/ansible/test_results -name "*.log" -exec echo "{}:" \; -exec head -n 5 {} \; -exec echo "" \;
```text
## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/rpm-package-tests.yml
name: RPM Package Tests

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      package_version:
        description: 'Package version to test (leave empty for latest)'
        required: false

jobs:
  test-rpm-installation:
    name: Test on ${{ matrix.platform.name }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        platform:
          - { name: fedora-41, image: fedora:41 }
          - { name: fedora-40, image: fedora:40 }
          - { name: rocky-9, image: rockylinux:9 }
          - { name: alma-9, image: almalinux:9 }
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

      - name: Run Ansible RPM package tests
        run: |
          ansible-playbook tests/rpm/ansible/run_single_platform.yml \
            -e "platform_name=${{ matrix.platform.name }}" \
            -e "base_image=${{ matrix.platform.image }}"

      - name: Upload test logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: rpm-test-logs-${{ matrix.platform.name }}
          path: tests/rpm/ansible/test_results/
```text
## Test Execution

### Local Testing with Ansible

```bash
# Quick smoke test on Fedora (uses Ansible)
make test-rpm

# Test specific platform (via Ansible playbook)
make test-rpm-rocky

# Comprehensive test across all platforms (Ansible orchestration)
make test-rpm-all

# View test results
make test-rpm-results
```text
### Manual Ansible Execution

```bash
# Run single platform test directly with Ansible
ansible-playbook tests/rpm/ansible/run_single_platform.yml \
    -e "platform_name=fedora-41" \
    -e "base_image=fedora:41"

# Run all platforms test
ansible-playbook tests/rpm/ansible/run_all_rpm_tests.yml

# Run with verbose output for debugging
ansible-playbook tests/rpm/ansible/run_single_platform.yml \
    -e "platform_name=fedora-41" \
    -e "base_image=fedora:41" \
    -vvv

# Run specific verification playbook inside container manually
docker run --rm -it dfakeseeder-rpm-test:fedora-41 \
    ansible-playbook /home/testuser/ansible/verify_rpm_package.yml -i /home/testuser/ansible/inventory/localhost
```text
### Manual Docker Testing (Interactive Debugging)

```bash
# Build test container with Ansible
docker build \
    --build-arg BASE_IMAGE=fedora:41 \
    -f tests/rpm/Dockerfile.rpm-test \
    -t dfakeseeder-rpm-test:fedora-41 \
    tests/rpm/

# Run Ansible playbook in container (automated)
docker run --rm dfakeseeder-rpm-test:fedora-41

# Run interactively for debugging (bash shell)
docker run --rm -it dfakeseeder-rpm-test:fedora-41 /bin/bash

# Inside interactive container, manually run Ansible playbook
# (from within container shell)
ansible-playbook /home/testuser/ansible/verify_rpm_package.yml \
    -i /home/testuser/ansible/inventory/localhost
```text
### CI/CD Execution

Tests run automatically via Ansible playbooks:
- On every release publication
- Can be triggered manually for specific versions
- Results uploaded to GitHub Actions artifacts
- Ansible provides structured, idempotent test execution
- Test logs saved in `tests/rpm/ansible/test_results/`

## Test Maintenance

### Regular Tasks

1. **After Each Release**: Run full RPM test suite via `make test-rpm-all`
2. **Weekly**: Spot check latest package on Fedora via `make test-rpm-fedora`
3. **Monthly**: Update Docker base images to latest versions in Ansible playbook variables
4. **Quarterly**: Add new distribution versions to `test_platforms` list in orchestration playbook

### Updating Tests

When adding new features:
1. Update Ansible verification playbook (`verify_rpm_package.yml`) with new test stages
2. Add new test tasks for desktop integration changes
3. Update CLI command verification list in playbook variables
4. Update documentation in this plan
5. Test changes with `make test-rpm` before committing

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
- ✅ RPM package installs on all supported platforms
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
4. Rebuild RPM package (increment version)
5. Re-run tests

## Best Practices

### DO
- ✅ Test in clean containers
- ✅ Use non-root user for testing when possible
- ✅ Verify desktop integration thoroughly
- ✅ Test on multiple RHEL-based distributions
- ✅ Check for missing system dependencies
- ✅ Verify CLI scripts are in PATH

### DON'T
- ❌ Test on host machine (not isolated)
- ❌ Skip platform-specific tests
- ❌ Ignore failed tests
- ❌ Test with development version
- ❌ Run all commands as root
- ❌ Skip desktop integration tests

## Troubleshooting

### Common Issues

**Issue**: Package not found in PATH after installation

**Solution**: Check if `/usr/bin` or `/usr/local/bin` is in PATH, verify RPM installed scripts to correct location

---

**Issue**: GTK4 import errors

**Solution**: Verify system dependencies installed (python3-gobject, gtk4)

---

**Issue**: Desktop file validation fails

**Solution**: Check desktop file format, verify .desktop file syntax

---

**Issue**: Icons not showing

**Solution**: Run `gtk-update-icon-cache`, check icon file permissions

---

## Summary

This RPM testing plan ensures that DFakeSeeder RPM packages work correctly for end users on Red Hat-based distributions by:

1. **Isolated Testing**: Docker containers prevent interference with development environment
2. **Multi-Platform Verification**: Tests across 4 RHEL-based distributions (Fedora, Rocky Linux, AlmaLinux)
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
1. Create `tests/rpm/ansible/` directory structure
2. Implement Dockerfile template with Ansible installation
3. Write Ansible verification playbook (`verify_rpm_package.yml`)
4. Write Ansible orchestration playbook (`run_all_rpm_tests.yml`)
5. Create Ansible inventory file for localhost testing
6. Add Makefile targets using ansible-playbook commands
7. Set up GitHub Actions workflow with Ansible integration
8. Install ansible-galaxy community.docker collection
9. Run initial test suite on current RPM package with `make test-rpm-all`
