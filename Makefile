.PHONY: all build install clean iso deps validate dev-setup smoke bundle test lint

all: deps build

deps:
	@echo "Installing build dependencies..."
	@which debootstrap >/dev/null || sudo apt-get install -y debootstrap
	@which qemu-img >/dev/null || sudo apt-get install -y qemu-utils
	@which xorriso >/dev/null || sudo apt-get install -y xorriso

build:
	@echo "Building PhantomOS..."
	@chmod +x build/build.sh
	@cd build && ./build.sh

validate:
	@echo "Validating PhantomOS sources..."
	@chmod +x build/build.sh
	@cd build && ./build.sh validate

dev-setup:
	@echo "Preparing local development environment..."
	@chmod +x build/dev-setup.sh
	@cd build && ./dev-setup.sh

smoke:
	@echo "Running local smoke tests..."
	@chmod +x build/smoke.sh
	@cd build && ./smoke.sh

test:
	@echo "Running unit tests..."
	@PYTHONPATH="$(PWD)" .venv/bin/python -m pytest tests/ -v

lint:
	@echo "Running linter..."
	@.venv/bin/python -m ruff check ai/ compatibility/ gui/ privacy/ system/ phantom_env.py || true

bundle:
	@echo "Creating a non-root developer bundle..."
	@chmod +x build/build.sh
	@cd build && ./build.sh bundle

install:
	@echo "Running post-install..."
	@chmod +x system/config/post-install.sh
	@sudo ./system/config/post-install.sh

iso:
	@echo "Creating ISO..."
	@cd build && ./build.sh

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/rootfs build/iso build/*.squashfs
	@rm -f iso/*.iso

help:
	@echo "PhantomOS Build System"
	@echo "======================"
	@echo "make deps    - Install build dependencies"
	@echo "make build   - Build the OS"
	@echo "make validate - Run static project validation"
	@echo "make dev-setup - Create a local Python virtualenv"
	@echo "make smoke   - Run the local LLM and terminal smoke test"
	@echo "make bundle  - Create a non-root PhantomOS devkit tarball"
	@echo "make install - Run post-install configuration"
	@echo "make iso     - Create bootable ISO"
	@echo "make clean   - Clean build artifacts"
