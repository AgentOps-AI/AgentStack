#!/bin/bash
export LANG=en_US.UTF-8
set -e

LOGO=$(cat <<'EOF'
    ___       ___       ___       ___       ___       ___       ___       ___       ___       ___   
   /\  \     /\  \     /\  \     /\__\     /\  \     /\  \     /\  \     /\  \     /\  \     /\__\  
  /::\  \   /::\  \   /::\  \   /:| _|_    \:\  \   /::\  \    \:\  \   /::\  \   /::\  \   /:/ _/_ 
 /::\:\__\ /:/\:\__\ /::\:\__\ /::|/\__\   /::\__\ /\:\:\__\   /::\__\ /::\:\__\ /:/\:\__\ /::- \__\\
 \/\::/  / \:\:\/__/ \:\:\/  / \/|::/  /  /:/\/__/ \:\:\/__/  /:/\/__/ \/\::/  / \:\ \/__/ \;:;- ,- 
   /:/  /   \::/  /   \:\/  /    |:/  /   \/__/     \::/  /   \/__/      /:/  /   \:\__\    |:|  |  
   \/__/     \/__/     \/__/     \/__/               \/__/               \/__/     \/__/     \|__|  
EOF
)

APP_NAME="agentstack"
VERSION="0.3.5"
REPO_URL="https://github.com/AgentOps-AI/AgentStack"
RELEASE_PATH_URL="$REPO_URL/archive/refs/tags"
CHECKSUM_URL=""  # TODO
PYTHON_VERSION=">=3.10,<3.13"
UV_INSTALLER_URL="https://astral.sh/uv/install.sh"
PYTHON_BIN_PATH=""  # set after a verified install is found
DEV_BRANCH=""  # set by --dev-branch flag
PRINT_VERBOSE=0
PRINT_QUIET=1

MSG_SUCCESS=$(cat <<EOF
✅ Setup complete!

To get started with AgentStack, run:
    exec \$SHELL
    agentstack init

For more information, run:
    agentstack docs -or- agentstack quickstart
EOF
)

MSG_ALREADY_INSTALLED=$(cat <<EOF
✅ AgentStack is already installed.
Run 'agentstack update' to update to the latest version.
EOF
)

usage() {
    cat <<EOF
agentstack-install.sh

The installer for AgentStack

This script installs uv the Python package manager, installs a compatible Python 
version ($PYTHON_VERSION), and installs AgentStack.

USAGE:
    agentstack-install.sh [OPTIONS]

OPTIONS:
    --version=<version>        Specify version to install (default: $VERSION)
    --python-version=<version> Specify Python version to install (default: $PYTHON_VERSION)
    --dev-branch=<branch>      Install from a specific git branch/commit/tag
    --verbose                  Enable verbose output
    --quiet                    Suppress output
    -h, --help                 Show this help message
EOF
}
# TODO allow user to specify install path with --target
# TODO allow user to specify Python version with --python-version
# TODO uninstall

say() {
    if [ "1" = "$PRINT_QUIET" ]; then
        echo -e "$1"
    fi
}

say_verbose() {
    if [ "1" = "$PRINT_VERBOSE" ]; then
        echo -e "[DEBUG] $1"
    fi
}

ACTIVITY_PID=""
_show_activity() {
    while true; do
        echo -n "."
        sleep 1
    done
}

show_activity() {
    if [ "1" = "$PRINT_QUIET" ] || [ "1" = "$PRINT_VERBOSE" ]; then
        return 0
    fi
    _show_activity &
    ACTIVITY_PID=$!
    # trap end_activity EXIT
    # trap 'kill $ACTIVITY_PID' INT
    # wait $ACTIVITY_PID
}

end_activity() {
    if [ -n "$ACTIVITY_PID" ]; then
        say ""  # newline after the dots
        kill $ACTIVITY_PID
    fi
}

err() {
    end_activity
    if [ "1" = "$PRINT_QUIET" ]; then
        local _red=$(tput setaf 1 2>/dev/null || echo '')
        local _reset=$(tput sgr0 2>/dev/null || echo '')
        say "\n${_red}[ERROR]${_reset}: $1" >&2
        say "\nRun with --verbose for more details."
        say "\nIf you need help, please feel free to open an issue:"
        say "\n  $REPO_URL/issues\n"
    fi
    exit 1
}

err_missing_cmd() {
    local _cmd_name=$1
    local _help_text=""
    local _platform=$(platform)

    if [ $_platform == "linux" ]; then
        if [ $_cmd_name == "gcc" ]; then
            _help_text="Hint: sudo apt-get install build-essential"
        else
            _help_text="Hint: sudo apt-get install $_cmd_name"
        fi
    elif [ $_platform == "macos" ]; then
        _help_text="Hint: brew install $_cmd_name"
    fi
    err "A required dependency is missing. Please install: $*\n$_help_text"
}

# Check if a command exists
check_cmd() {
    command -v "$1" > /dev/null 2>&1
    return $?
}

# Check if a command exists and print an error message if it doesn't
need_cmd() {
    if ! check_cmd "$1"; then
        err_missing_cmd $1
    fi
}

# Check if one of multiple commands exist and print an error message if none do
need_cmd_option() {
    local _found=0
    for cmd in "$@"; do
        if check_cmd "$cmd"; then
            _found=1
            break
        fi
    done

    if [ $_found -eq 0 ]; then
       err_missing_cmd $1
    fi
}

ensure() {
    if ! "$@"; then err "command failed: $*"; fi
}

platform() {
    case "$(uname -s)" in
        Linux*)     echo "linux" ;;
        Darwin*)    echo "macos" ;;
        CYGWIN*)    echo "cygwin" ;;
        *)          echo "unknown" ;;
    esac
}

# Check for required commands
check_dependencies() {
    say "Checking dependencies..."
    need_cmd mkdir
    need_cmd mktemp
    need_cmd chmod
    need_cmd rm
    need_cmd grep
    need_cmd awk
    need_cmd cat

    need_cmd_option curl wget
    need_cmd_option tar unzip
    need_cmd gcc  # need gcc to install psutil
    say "Dependencies are met."
}

# Install uv
install_uv() {
    if check_cmd uv; then
        say_verbose "uv is already installed."
        return 0
    else
        say "Installing uv..."
    fi
    show_activity

    # download with curl or wget
    local _install_cmd
    if check_cmd curl; then
        say_verbose "Running uv installer with curl"
        _install_cmd="curl -LsSf $UV_INSTALLER_URL | sh"
    elif check_cmd wget; then
        say_verbose "Running uv installer with wget"
        _install_cmd="wget -qO- $UV_INSTALLER_URL | sh"
    else
        err "neither curl nor wget is available"
    fi

    # run the installer
    say_verbose "$_install_cmd"
    local _output=$(eval "$_install_cmd" 2>&1)
    local _retval=$?
    say_verbose "$_output"
    if [ $_retval -ne 0 ]; then
        err "uv installation failed: $_output"
    fi

    # verify uv installation
    local _uv_version
    _uv_version="$(uv --version 2>/dev/null)" || {
        _uv_version=0
    }

    end_activity
    if [ -z "$_uv_version" ]; then
        err "uv installation failed."
    else
        say "📦 $_uv_version installed successfully!"
    fi
}

# Install the required Python version
setup_python() {
    PYTHON_BIN_PATH="$(uv python find "$PYTHON_VERSION" 2>/dev/null)" || {
        PYTHON_BIN_PATH=""
    }
    if [ -x "$PYTHON_BIN_PATH" ]; then
        local _python_version="$($PYTHON_BIN_PATH --version 2>&1)"
        say "Python $_python_version is available."
        return 0
    else
        show_activity
    
        say "Installing Python $PYTHON_VERSION..."
        uv python install "$PYTHON_VERSION" --preview 2>/dev/null || {
            err "Failed to install Python"
        }
        PYTHON_BIN_PATH="$(uv python find "$PYTHON_VERSION")" || {
            err "Failed to find Python"
        }

        end_activity
    fi

    if [ -x "$PYTHON_BIN_PATH" ]; then
        local _python_version="$($PYTHON_BIN_PATH --version 2>&1)"
        say "🐍 Python $_python_version installed successfully!"
    else
        err "Failed to install Python"
    fi
}

# Install an official release of the app
install_release() {
    say "Installing $APP_NAME..."
    show_activity

    local _zip_ext
    if check_cmd tar; then
        _zip_ext=".tar.gz"
    elif check_cmd unzip; then
        _zip_ext=".zip"
    else
        err "could not find tar or unzip"
    fi

    local _url="${RELEASE_PATH_URL}/${VERSION}${_zip_ext}"
    local _dir="$(ensure mktemp -d)" || return 1
    local _file="$_dir/input$_zip_ext"
    local _checksum_file="$_dir/checksum"

    say_verbose "downloading $APP_NAME $VERSION" 1>&2
    say_verbose "  from $_url" 1>&2
    say_verbose "  to $_file" 1>&2

    # download tar or zip
    if ! download_file "$_url" "$_file"; then
        say_verbose "failed to download $_url"
        err "Failed to download $APP_NAME $VERSION"
    fi

    # download checksum
    if ! download_file "$CHECKSUM_URL" "$_checksum_file"; then
        say_verbose "failed to download checksum file: $CHECKSUM_URL"
        say "Skipping checksum verification"
    fi

    # verify checksum
    # github action generates checksums in the following format:
    # 0.3.4.tar.gz	ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb
    # 0.3.4.zip	0263829989b6fd954f72baaf2fc64bc2e2f01d692d4de72986ea808f6e99813f
    if [ -f $_checksum_file ]; then
        # TODO this needs to be tested. 
        say_verbose "verifying checksum"
        local _checksum_value="$(cat "$_checksum_file" | grep "${VERSION}${_zip_ext}" | awk '{print $2}')"
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
            err "unknown archive format"
            ;;
    esac

    # install & cleanup
    setup_app "$_dir"
    rm -rf "$_dir"
    end_activity
    say "💥 $APP_NAME $VERSION installed successfully!"
}

# Install a specific branch/commit/tag from the git repo
install_dev_branch() {
    need_cmd git
    if [ -z "$DEV_BRANCH" ]; then
        err "DEV_BRANCH is not set"
    fi

    say "Installing $APP_NAME..."
    show_activity
    local _dir="$(ensure mktemp -d)" || return 1

    # clone from git
    local _git_url="$REPO_URL.git"
    local _git_cmd="git clone --depth 1 $_git_url $_dir"
    say_verbose "$_git_cmd"
    local _git_out="$($_git_cmd 2>&1)"
    say_verbose "$_git_out"
    if [ $? -ne 0 ] || echo "$_git_out" | grep -qi "error\|fatal"; then
        err "Failed to clone git repo."
    fi

    # checkout
    local _tag=${DEV_BRANCH#*:} # just the tag name (pull/123/head:pr-123 -> pr-123)
    ensure git -C $_dir fetch origin $DEV_BRANCH
    ensure git -C $_dir checkout $_tag

    # install & cleanup
    setup_app "$_dir"
    rm -rf "$_dir"
    end_activity
    say "🔧 $APP_NAME @ $DEV_BRANCH installed successfully!"
}

# Install the app in the user's site-packages directory and add a executable
setup_app() {
    local _dir="$1"
    local _packages_dir="$($PYTHON_BIN_PATH -m site --user-site 2>/dev/null)" || {
        err "Failed to find user site packages directory"
    }
    say_verbose "Installing to $_packages_dir"
    local _install_cmd="uv pip install --python="$PYTHON_BIN_PATH" --target="$_packages_dir" --directory="$_dir" ."
    say_verbose "$_install_cmd"
    local _install_out="$(eval "$_install_cmd" 2>&1)"
    say_verbose "$_install_out"
    if [ $? -ne 0 ] || echo "$_install_out" | grep -qi "error\|failed\|exception"; then
        err "Failed to install $APP_NAME."
    fi
    
    make_python_bin "$HOME/.local/bin/$APP_NAME"
    update_path "$HOME/.local/bin"
    say_verbose "Added bin to ~/.local/bin/$APP_NAME"

    # verify installation
    ensure "$APP_NAME" --version > /dev/null
}

# Update PATH in shell config files
update_path() {
    local new_path="$1"
    
    # update for current session
    export PATH="$new_path:$PATH"
    
    # update for each shell
    local config_files=(
        "$HOME/.bashrc"          # bash
        "$HOME/.zshrc"           # ssh
        "$HOME/.profile"         # POSIX fallback (sh, ksh, etc.)
    )
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            if ! grep -E "^[^#]*export[[:space:]]+PATH=.*(:$new_path|$new_path:|$new_path\$)" "$config_file" >/dev/null 2>&1; then
                echo "export PATH=\"$new_path:\$PATH\"" >> "$config_file"
                say_verbose "Added PATH $new_path to $config_file"
            else
                say_verbose "PATH $new_path already in $config_file"
            fi
        fi
    done
}

# Create a bin file for the app. Assumes entrypoint is main.py:main
make_python_bin() {
    local _program_bin="$1"
    local _bin_content=$(cat <<EOF
#!/${PYTHON_BIN_PATH}
# -*- coding: utf-8 -*-
import re
import sys
from ${APP_NAME}.main import main
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
EOF
    )

    say_verbose "Creating bin file at $_program_bin"
    echo "$_bin_content" > $_program_bin
    chmod +x $_program_bin
}

# Download a file. Try curl first, if not installed, use wget instead.
download_file() {
    local _url="$1"
    local _file="$2"
    local _cmd

    if check_cmd curl; then
        # use curl
        _cmd="curl -sSfL "$_url" -o "$_file"" 
    elif check_cmd wget; then
        # use wget
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
    _calculated_checksum="$(sha256sum -b "$_file" | awk '{print $1}')"

    if [ "$_calculated_checksum" != "$_checksum_value" ]; then
        err "checksum mismatch
            want: $_checksum_value
            got:  $_calculated_checksum"
    fi
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version=*)
                VERSION="${1#*=}"
                shift
                ;;
            --version)
                if [[ -z "$2" || "$2" == -* ]]; then
                    err "Error: --version requires a value"
                    usage
                    exit 1
                fi
                VERSION="$2"
                shift 2
                ;;
            --python-version=*)
                PYTHON_VERSION="${1#*=}"
                shift
                ;;
            --python-version)
                if [[ -z "$2" || "$2" == -* ]]; then
                    err "Error: --python-version requires a value"
                    usage
                    exit 1
                fi
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --dev-branch=*)
                DEV_BRANCH="${1#*=}"
                shift
                ;;
            --dev-branch)
                if [[ -z "$2" || "$2" == -* ]]; then
                    err "Error: --dev-branch requires a value"
                    usage
                    exit 1
                fi
                DEV_BRANCH="$2"
                shift 2
                ;;
            --verbose)
                PRINT_VERBOSE=1
                shift
                ;;
            --quiet)
                PRINT_QUIET=0
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                err "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [[ -z "$COMMAND" ]]; then
                    COMMAND="$1"
                else
                    err "Unexpected argument: $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

main() {
    parse_args "$@"
    
    say "$LOGO\n"
    
    if check_cmd $APP_NAME; then
        say "\n$MSG_ALREADY_INSTALLED\n"
        exit 0
    fi

    say "Starting installation..."
    check_dependencies
    install_uv
    setup_python
    if [ -n "$DEV_BRANCH" ]; then
        install_dev_branch
    else
        install_release
    fi
    
    say "\n$MSG_SUCCESS\n"
    exit 0
}

main "$@"
