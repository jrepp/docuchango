#!/bin/bash
#
# Docuchango Installer
# Install docuchango documentation validation framework
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/jrepp/docuchango/main/install.sh | bash
#   Or locally: ./install.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.10"
INSTALL_METHOD="pip"  # or "uv" or "pipx"

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}     Docuchango Installer v0.1.0      ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▸${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_python() {
    print_step "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python ${PYTHON_MIN_VERSION} or higher from https://www.python.org/"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Found Python ${PYTHON_VERSION}"

    # Check version
    REQUIRED_VERSION=$(echo "$PYTHON_MIN_VERSION" | awk -F. '{printf "%d%02d", $1, $2}')
    CURRENT_VERSION=$(echo "$PYTHON_VERSION" | awk -F. '{printf "%d%02d", $1, $2}')

    if [ "$CURRENT_VERSION" -lt "$REQUIRED_VERSION" ]; then
        print_error "Python ${PYTHON_MIN_VERSION} or higher is required (found ${PYTHON_VERSION})"
        exit 1
    fi
}

check_pip() {
    print_step "Checking pip installation..."

    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not installed"
        echo "Installing pip..."
        python3 -m ensurepip --upgrade || {
            print_error "Failed to install pip"
            echo "Please install pip manually: https://pip.pypa.io/en/stable/installation/"
            exit 1
        }
    fi

    print_success "pip is available"
}

check_pipx() {
    print_step "Checking for pipx (recommended for CLI tools)..."

    if command -v pipx &> /dev/null; then
        PIPX_VERSION=$(pipx --version 2>&1 | head -1)
        print_success "Found pipx ${PIPX_VERSION}"
        INSTALL_METHOD="pipx"
        return 0
    else
        print_warning "pipx not found (recommended for CLI tools)."
        echo "          pipx installs tools in isolated environments with automatic PATH setup."
        echo "          To install pipx: python3 -m pip install --user pipx && python3 -m pipx ensurepath"
        echo "          Or visit: https://pipx.pypa.io/stable/installation/"
        echo ""
        return 1
    fi
}

check_uv() {
    print_step "Checking for uv (optional, faster installer)..."

    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | awk '{print $2}')
        print_success "Found uv ${UV_VERSION}"
        INSTALL_METHOD="uv"
    else
        print_warning "uv not found (optional). Will use pip for installation."
        echo "          To install uv later: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
}

install_docuchango() {
    print_step "Installing docuchango..."

    if [ "$INSTALL_METHOD" = "pipx" ]; then
        echo "Using pipx for isolated installation..."
        if [ -d ".git" ]; then
            # Local development install
            pipx install -e . || {
                print_error "Installation failed with pipx"
                exit 1
            }
        else
            # Install from PyPI
            pipx install docuchango || {
                print_error "Installation failed with pipx"
                exit 1
            }
        fi
    elif [ "$INSTALL_METHOD" = "uv" ]; then
        echo "Using uv for faster installation..."
        if [ -d ".git" ]; then
            # Local development install
            uv pip install -e . || {
                print_error "Installation failed with uv"
                exit 1
            }
        else
            # Install from PyPI
            uv pip install docuchango || {
                print_error "Installation failed with uv"
                exit 1
            }
        fi
    else
        echo "Using pip for installation..."
        if [ -d ".git" ]; then
            # Local development install
            python3 -m pip install -e . || {
                print_error "Installation failed with pip"
                exit 1
            }
        else
            # Install from PyPI
            python3 -m pip install docuchango || {
                print_error "Installation failed with pip"
                exit 1
            }
        fi
    fi

    print_success "docuchango installed successfully"
}

verify_installation() {
    print_step "Verifying installation..."

    if ! command -v docuchango &> /dev/null; then
        print_warning "docuchango command not found in PATH"
        echo ""
        echo "You may need to add the following to your PATH:"

        if [ -d "$HOME/.local/bin" ]; then
            echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi

        if python3 -c "import site; print(site.USER_BASE)" &> /dev/null; then
            USER_BASE=$(python3 -c "import site; print(site.USER_BASE)")
            echo "  export PATH=\"${USER_BASE}/bin:\$PATH\""
        fi

        echo ""
        echo "Add this to your ~/.bashrc, ~/.zshrc, or equivalent shell config file."
        echo ""
        return 1
    fi

    # Test the command
    DOCUCHANGO_VERSION=$(docuchango --version 2>&1 || echo "unknown")
    print_success "docuchango is available: ${DOCUCHANGO_VERSION}"

    # Test help command
    if docuchango --help &> /dev/null; then
        print_success "docuchango commands are working"
    else
        print_warning "docuchango command exists but help failed"
        return 1
    fi

    return 0
}

show_next_steps() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. View the bootstrap guide:"
    echo -e "   ${BLUE}docuchango bootstrap${NC}"
    echo ""
    echo "2. View agent instructions:"
    echo -e "   ${BLUE}docuchango bootstrap --guide agent${NC}"
    echo ""
    echo "3. Validate your documentation:"
    echo -e "   ${BLUE}cd your-project${NC}"
    echo -e "   ${BLUE}docuchango validate${NC}"
    echo ""
    echo "4. Get help:"
    echo -e "   ${BLUE}docuchango --help${NC}"
    echo ""
    echo "For more information, visit:"
    echo "  https://github.com/jrepp/docuchango"
    echo ""
}

main() {
    print_header

    check_python
    check_pip

    # Check for pipx first (recommended for CLI tools)
    # If not found, check for uv as alternative
    if ! check_pipx; then
        check_uv
    fi

    echo ""
    install_docuchango

    echo ""
    if verify_installation; then
        show_next_steps
    else
        echo ""
        print_warning "Installation completed but verification had issues"
        echo "Try running: docuchango --version"
        echo ""
        echo "If the command is not found, you may need to:"
        echo "1. Restart your shell"
        echo "2. Add Python's bin directory to your PATH"
        echo ""
        if [ "$INSTALL_METHOD" = "pipx" ]; then
            echo "For pipx installations, run: pipx ensurepath"
        fi
        echo ""
    fi
}

# Run main installation
main
