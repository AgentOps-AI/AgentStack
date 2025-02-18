#!/bin/bash
set -e

LOGO=$(cat <<EOF
    ___       ___       ___       ___       ___       ___       ___       ___       ___       ___   
   /\  \     /\  \     /\  \     /\__\     /\  \     /\  \     /\  \     /\  \     /\  \     /\__\  
  /::\  \   /::\  \   /::\  \   /:| _|_    \:\  \   /::\  \    \:\  \   /::\  \   /::\  \   /:/ _/_ 
 /::\:\__\ /:/\:\__\ /::\:\__\ /::|/\__\   /::\__\ /\:\:\__\   /::\__\ /::\:\__\ /:/\:\__\ /::-"\__\\
 \/\::/  / \:\:\/__/ \:\:\/  / \/|::/  /  /:/\/__/ \:\:\/__/  /:/\/__/ \/\::/  / \:\ \/__/ \;:;-",-"
   /:/  /   \::/  /   \:\/  /    |:/  /   \/__/     \::/  /   \/__/      /:/  /   \:\__\    |:|  |  
   \/__/     \/__/     \/__/     \/__/               \/__/               \/__/     \/__/     \|__|  
EOF
)

APP_NAME="agentstack"
VERSION="0.3.5"
RELEASE_PATH_URL="https://github.com/AgentOps-AI/AgentStack/archive/refs/tags"
CHECKSUM_URL=""
REQUIRED_PYTHON_VERSION=">=3.10,<3.13"
PYTHON_BIN_PATH=""
UV_INSTALLER_URL="https://astral.sh/uv/install.sh"
PRINT_VERBOSE=0
PRINT_QUIET=1

MOTD=$(cat <<EOF
Setup complete!
You may need to restart your shell or run:
    export PATH="\$HOME/.local/bin:\$PATH"

To get started with $APP_NAME, try:
    $APP_NAME init

EOF
)

usage() {
    cat <<EOF
agentstack-install.sh

The installer for AgentStack

This script installs uv the Python package manager, installs a compatible Python 
version ($REQUIRED_PYTHON_VERSION), and installs AgentStack $AGENTSTACK_VERSION.

USAGE:
    agentstack-install.sh [OPTIONS]

OPTIONS:
    --version VERSION    Specify version to install (default: latest)
    --verbose            Enable verbose output
    --quiet              Suppress output
    -h, --help           Show this help message
EOF
}

say() {
    if [ "1" = "$PRINT_QUIET" ]; then
        echo "$1"
    fi
}

say_verbose() {
    if [ "1" = "$PRINT_VERBOSE" ]; then
        echo "[DEBUG] $1"
    fi
}

err() {
    if [ "0" = "$PRINT_QUIET" ]; then
        local red
        local reset
        red=$(tput setaf 1 2>/dev/null || echo '')
        reset=$(tput sgr0 2>/dev/null || echo '')
        say "${red}ERROR${reset}: $1" >&2
    fi
    exit 1
}

# Check if a command exists and print an error message if it doesn't
need_cmd() {
    if ! check_cmd "$1"
    then err "need '$1' (command not found)"
    fi
}

# Check if a command exists
check_cmd() {
    command -v "$1" > /dev/null 2>&1
    return $?
}

# Run a command that should never fail. If the command fails execution
# will immediately terminate with an error showing the failing command.
ensure() {
    if ! "$@"; then err "command failed: $*"; fi
}

# Check for required commands
check_dependencies() {
    need_cmd mkdir
    need_cmd mktemp
    need_cmd chmod
    need_cmd rm
    need_cmd tar
    need_cmd grep
    need_cmd awk
    need_cmd cat

    # need gcc to install psutil which is a sub-dependency of agentstack
    need_cmd gcc
}

# Install uv
install_uv() {
    if check_cmd uv; then
        say_verbose "uv is already installed."
        return 0
    else
        say "Installing uv..."
    fi

    # determine which downloader to use
    local _install_cmd
    if check_cmd curl; then
        say_verbose "Running uv installer with curl"
        _install_cmd="curl -LsSf $UV_INSTALLER_URL | sh"
    elif check_cmd wget; then
        say_verbose "Running uv installer with wget"
        _install_cmd="wget -qO- $UV_INSTALLER_URL | sh"
    else
        err "Neither curl nor wget is available. Please install one of them."
    fi

    # run the installer
    local _output=$(eval "$_install_cmd" 2>&1)
    local _retval=$?
    say_verbose "$_output"
    if [ $_retval -ne 0 ]; then
        err "uv installation failed: $_output"
    fi

    # ensure uv is in PATH
    if ! check_cmd uv; then
        say_verbose "Adding ~/.local/bin to PATH"
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # verify uv installation
    local _uv_version
    _uv_version="$(uv --version 2>/dev/null)" || {
        _uv_version=0
    }
    if [ -z "$_uv_version" ]; then
        err "uv installation failed. Please ensure ~/.local/bin is in your PATH"
    else
        say "$_uv_version installed successfully!"
    fi
}

# Install the required Python version
setup_python() {
    PYTHON_BIN_PATH="$(uv python find "$REQUIRED_PYTHON_VERSION" 2>/dev/null)" || {
        PYTHON_BIN_PATH=""
    }
    if [ -x "$PYTHON_BIN_PATH" ]; then
        say "Python $REQUIRED_PYTHON_VERSION is already installed."
        return 0
    else
        say "Installing Python $REQUIRED_PYTHON_VERSION..."
        uv python install "$REQUIRED_PYTHON_VERSION" --preview 2>/dev/null || {
            err "Failed to install Python"
        }
        PYTHON_BIN_PATH="$(uv python find "$REQUIRED_PYTHON_VERSION")" || {
            err "Failed to find Python"
        }
    fi
    
    if [ -x "$PYTHON_BIN_PATH" ]; then
        local _python_version="$($PYTHON_BIN_PATH --version 2>&1)"
        say "Python $_python_version installed successfully!"
    else
        err "Failed to install Python $REQUIRED_PYTHON_VERSION"
    fi
}

# Install the application
install_app() {
    say "Installing $APP_NAME..."
    
    local _zip_ext
    _zip_ext=".tar.gz"  # TODO do we need to fallback to .zip?

    local _url="$RELEASE_PATH_URL/$VERSION$_zip_ext"
    local _dir
    _dir="$(ensure mktemp -d)" || return 1
    local _file="$_dir/input$_zip_ext"
    local _checksum_file="$_dir/checksum"

    say_verbose "downloading $APP_NAME $VERSION" 1>&2
    say_verbose "  from $_url" 1>&2
    say_verbose "  to $_file" 1>&2

    ensure mkdir -p "$_dir"

    # download tar or zip
    if ! downloader "$_url" "$_file"; then
        say_verbose "failed to download $_url"
        sy "Failed to download $APP_NAME $VERSION"
        say "(this may be a standard network error, but it may also indicate"
        say "that $APP_NAME's release process is not working. When in doubt"
        say "please feel free to open an issue!)"
        exit 1
    fi

    # download checksum
    if ! downloader "$CHECKSUM_URL" "$_checksum_file"; then
        say_verbose "failed to download checksum file: $CHECKSUM_URL"
        say "Skipping checksum verification"
    fi

    # verify checksum
    # github action generates checksums in the following format:
    # 0.3.4.tar.gz	ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb
    # 0.3.4.zip	0263829989b6fd954f72baaf2fc64bc2e2f01d692d4de72986ea808f6e99813f
    if [ -e $_checksum_file ]; then
        # TODO this needs to be tested. 
        say_verbose "verifying checksum"
        local _all_checksums="$(cat "$_checksum_file")"
        local _checksum_value="$(echo "$_all_checksums" | grep "$VERSION$_zip_ext" | awk '{print $1}')"
        verify_sha256_checksum "$_file" "$_checksum_value"
    fi

    # unpack the archive
    case "$_zip_ext" in
        ".zip")
            ensure unzip -q "$_file" -d "$_dir"
            ;;
        ".tar."*)
            ensure tar xf "$_file" --strip-components 1 -C "$_dir"
            ;;
        *)
            err "unknown archive format: $_zip_ext"
            ;;
    esac

    # run setup
    local _packages_dir="$($PYTHON_BIN_PATH -m site --user-site 2>/dev/null)" || {
        err "Failed to find user site packages directory"
    }
    say_verbose "Installing to $_packages_dir"
    local _install_out
    _install_out="$(uv pip install --python=$PYTHON_BIN_PATH --target=$_packages_dir --directory=$_dir . 2>&1)" || {
        err "Failed to install $APP_NAME"
    }
    say_verbose "$_install_out"
    make_python_bin "$PYTHON_BIN_PATH" "$HOME/.local/bin/$APP_NAME"

    # verify installation
    ensure "$APP_NAME" --version > /dev/null

    # cleanup
    rm -rf "$_dir"
    say "$APP_NAME installed successfully!"
}

# Manually create a bin file for the app
# $1: python bin path
# $2: program bin path
make_python_bin() {
    local _python_bin="$1"
    local _program_bin="$2"
    local _bin_content=$(cat <<EOF
#!/${_python_bin}
# -*- coding: utf-8 -*-
import re
import sys
from agentstack.main import main
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
EOF
    )

    say_verbose "Creating bin file at $_program_bin"
    echo "$_bin_content" > $_program_bin
    chmod +x $_program_bin
}

# This wraps curl or wget. Try curl first, if not installed, use wget instead.
downloader() {
    local _url="$1"
    local _file="$2"
    local _cmd

    if check_cmd curl; then
        _cmd="curl -sSfL "$_url" -o "$_file"" 
    elif check_cmd wget; then
        _cmd="wget -q "$_url" -O "$_file""
    else
        err "need curl or wget (command not found)"
        return 1
    fi

    local _out
    local _out="$($_cmd 2>&1)" || {
        say_verbose "$_out"
        return 1
    }
    return 0
}

verify_sha256_checksum() {
    local _file="$1"
    local _checksum_value="$2"
    local _calculated_checksum

    if [ -z "$_checksum_value" ]; then
        return 0
    fi

    if ! check_cmd sha256sum; then
        say "skipping sha256 checksum verification (requires 'sha256sum' command)"
        return 0
    fi
    _calculated_checksum="$(sha256sum -b "$_file" | awk '{printf $1}')"

    if [ "$_calculated_checksum" != "$_checksum_value" ]; then
        err "checksum mismatch
            want: $_checksum_value
            got:  $_calculated_checksum"
    fi
}

# Parse command line arguments
parse_args() {
    for arg in "$@"; do
        case "$arg" in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --verbose)
                PRINT_VERBOSE=1
                ;;
            --quiet)
                PRINT_QUIET=0
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                err "Unknown argument: $1"
                ;;
        esac
    done
}

main() {
    parse_args "$@"
    
    say "$LOGO"
    say ""
    say "Starting installation..."
    
    check_dependencies
    install_uv
    setup_python
    install_app
    
    say ""
    say "$MOTD"
}

main "$@"