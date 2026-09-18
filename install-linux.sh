#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# BlueWatch – Linux (systemd) Install / Uninstall / Reset
# Installs BlueWatch into its own virtual environment and registers
# a systemd service so it starts automatically at boot.
#
# Works on Raspberry Pi OS / Debian / Ubuntu (apt). On other distros,
# install BlueZ, Python 3.11+ (with venv) yourself, then run this.
#
# Usage:
#   ./install-linux.sh [install]            Install (or upgrade) and start.
#   ./install-linux.sh uninstall [--purge]  Stop and remove service + venv.
#                                           --purge also deletes the data.
#   ./install-linux.sh reset [--purge]      Uninstall, then reinstall.
#
# Layout:
#   /opt/bluewatch/venv        Python virtual environment
#   /var/lib/bluewatch         Database and cache (BLUEWATCH_DATA_DIR)
#   /etc/systemd/system/bluewatch.service
# ──────────────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; }
step()  { printf "\n${CYAN}── %s${NC}\n" "$*"; }

usage() {
    cat <<'USAGE'
BlueWatch – Linux Install / Uninstall / Reset

Usage:
  ./install-linux.sh [install]            Install (or upgrade) and start.
  ./install-linux.sh uninstall [--purge]  Stop and remove service + venv.
                                          --purge also deletes the data.
  ./install-linux.sh reset [--purge]      Uninstall, then reinstall.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/bluewatch"
VENV_DIR="${INSTALL_DIR}/venv"
DATA_DIR="/var/lib/bluewatch"
SERVICE_NAME="bluewatch"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
WEB_PORT=8080  # default dashboard port

# ── Verify Linux + systemd ───────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
    error "This script is for Linux only (use ./install.sh on macOS)."
    exit 1
fi
if ! command -v systemctl &>/dev/null; then
    error "systemd (systemctl) not found. Use Docker instead, see README."
    exit 1
fi

# ── Argument parsing (before sudo so --help works unprivileged) ──
COMMAND="install"
PURGE="false"
for arg in "$@"; do
    case "${arg}" in
        install|uninstall|reset) COMMAND="${arg}" ;;
        --purge)                 PURGE="true" ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Unknown argument: ${arg} (use --help)"
            exit 1
            ;;
    esac
done

# ── Re-run as root if needed ─────────────────────────────────
if [[ "${EUID}" -ne 0 ]]; then
    if command -v sudo &>/dev/null; then
        info "Root privileges needed, re-running with sudo …"
        exec sudo -E "${BASH_SOURCE[0]}" "$@"
    fi
    error "Run as root (sudo not found)."
    exit 1
fi

# ── Helpers ──────────────────────────────────────────────────
# Resolve a usable python3 interpreter (>= 3.11).
find_python() {
    local candidate
    for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
        if command -v "${candidate}" &>/dev/null; then
            if "${candidate}" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 11) else 1)' &>/dev/null; then
                printf '%s' "${candidate}"
                return 0
            fi
        fi
    done
    return 1
}

# ── Uninstall ────────────────────────────────────────────────
do_uninstall() {
    local purge="${1:-false}"

    step "Uninstalling bluewatch"
    if systemctl list-unit-files "${SERVICE_NAME}.service" &>/dev/null; then
        systemctl disable --now "${SERVICE_NAME}" 2>/dev/null || true
    fi
    if [[ -f "${SERVICE_PATH}" ]]; then
        rm -f "${SERVICE_PATH}"
        info "Removed ${SERVICE_PATH}"
    fi
    if [[ -d "${SERVICE_PATH}.d" ]]; then
        rm -rf "${SERVICE_PATH}.d"
        info "Removed ${SERVICE_PATH}.d"
    fi
    systemctl daemon-reload

    if [[ -d "${INSTALL_DIR}" ]]; then
        rm -rf "${INSTALL_DIR}"
        info "Removed ${INSTALL_DIR}"
    fi

    if [[ "${purge}" == "true" ]]; then
        [[ -d "${DATA_DIR}" ]] && rm -rf "${DATA_DIR}" && info "Purged data ${DATA_DIR}"
    else
        info "Kept data (${DATA_DIR}). Use --purge to remove it."
    fi

    printf "\n${GREEN}✔ BlueWatch has been uninstalled.${NC}\n"
}

# ── Install ──────────────────────────────────────────────────
do_install() {
    # ── Step 1: Prerequisites ───────────────────────────────
    step "1/5  Installing prerequisites"

    if command -v apt-get &>/dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        local apt_log="/tmp/bluewatch-apt.log"
        if ! { apt-get update -qq && apt-get install -y -qq bluez python3 python3-venv python3-pip; } >"${apt_log}" 2>&1; then
            error "apt-get failed, last lines of ${apt_log}:"
            tail -n 15 "${apt_log}" >&2
            exit 1
        fi
        info "BlueZ and Python installed via apt."
    else
        warn "apt-get not found: make sure BlueZ, Python 3.11+ and python3-venv are installed."
    fi

    local python_bin
    if ! python_bin="$(find_python)"; then
        error "Python 3.11+ not found. Install it with your package manager and re-run."
        exit 1
    fi
    info "Python $(${python_bin} -c 'import sys; print("%d.%d" % sys.version_info[:2])') (${python_bin}) ✓"

    if ! "${python_bin}" -c 'import venv, ensurepip' &>/dev/null; then
        error "The Python venv module is missing. On Debian/Ubuntu: apt install python3-venv"
        exit 1
    fi

    systemctl enable --now bluetooth 2>/dev/null || warn "Could not enable the bluetooth service, check BlueZ."

    # ── Step 2: Directories ─────────────────────────────────
    step "2/5  Setting up directories"
    mkdir -p "${INSTALL_DIR}" "${DATA_DIR}"
    info "Venv:  ${VENV_DIR}"
    info "Data:  ${DATA_DIR}"

    # ── Step 3: Virtual environment ─────────────────────────
    step "3/5  Creating virtual environment"
    if [[ -d "${VENV_DIR}" ]]; then
        info "Existing venv found, upgrading …"
    else
        "${python_bin}" -m venv "${VENV_DIR}"
        info "Created ${VENV_DIR}"
    fi
    "${VENV_DIR}/bin/pip" install --upgrade pip --quiet

    # ── Step 4: Install bluewatch ───────────────────────────
    step "4/5  Installing bluewatch package"
    "${VENV_DIR}/bin/pip" install "${SCRIPT_DIR}[metrics]" --quiet
    info "Installed bluewatch into ${VENV_DIR}"

    # ── Step 5: systemd service ─────────────────────────────
    step "5/5  Configuring systemd service"
    if [[ ! -f "${SCRIPT_DIR}/bluewatch.service" ]]; then
        error "bluewatch.service not found next to this script."
        exit 1
    fi
    install -m 644 "${SCRIPT_DIR}/bluewatch.service" "${SERVICE_PATH}"
    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}" >/dev/null 2>&1
    systemctl restart "${SERVICE_NAME}"
    info "Service installed, enabled and started."

    # ── Verify ──────────────────────────────────────────────
    info "Waiting for the web dashboard …"
    local i ok="false"
    for i in $(seq 1 30); do
        if command -v curl &>/dev/null && curl -fs -o /dev/null --max-time 2 "http://127.0.0.1:${WEB_PORT}/"; then
            ok="true"
            break
        fi
        if ! command -v curl &>/dev/null && systemctl is-active --quiet "${SERVICE_NAME}" && [[ "${i}" -ge 8 ]]; then
            ok="true"
            break
        fi
        sleep 2
    done

    if [[ "${ok}" == "true" ]]; then
        printf "\n${GREEN}✔ BlueWatch is running!${NC}\n"
    else
        warn "The dashboard did not answer yet. Check the log:"
        warn "  journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
    fi

    cat <<EOF

────────────────────────────────────────────
  BlueWatch is installed and starts at boot.

  Dashboard:  http://<this-machine>:${WEB_PORT}

  Commands:
    sudo systemctl status  ${SERVICE_NAME}
    sudo systemctl restart ${SERVICE_NAME}
    journalctl -u ${SERVICE_NAME} -f

  Uninstall:           ./install-linux.sh uninstall
  Uninstall + wipe:    ./install-linux.sh uninstall --purge
  Upgrade:             git pull && ./install-linux.sh

  Data:  ${DATA_DIR}
────────────────────────────────────────────
EOF
}

case "${COMMAND}" in
    install)
        do_install
        ;;
    uninstall)
        do_uninstall "${PURGE}"
        ;;
    reset)
        do_uninstall "${PURGE}"
        do_install
        ;;
esac
