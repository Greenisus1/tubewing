#!/bin/sh
# tubewing: a tiny kiosk desktop for watching YouTube on a console Pi.
# One mini graphical session (cage compositor + Chromium fullscreen) -
# no desktop environment installed, nothing to configure.
set -eu

VERSION="1.0.0"
URL_MAIN="https://www.youtube.com"
URL_TV="https://www.youtube.com/tv"
DRY=0
[ "${1:-}" = "--dry-run" ] && { DRY=1; shift; }
[ "${TUBEWING_DRY_RUN:-0}" = "1" ] && DRY=1

say() { printf '%s\n' "$*"; }

as_root() {
    if [ "$DRY" = 1 ]; then say "  plan: sudo $*";
    elif [ "$(id -u)" -eq 0 ]; then "$@";
    else sudo "$@"; fi
}

cmd_install() {
    say "tubewing $VERSION - install"
    say "Installing the mini desktop (cage) + Chromium + sound (pipewire)..."
    say "This is a big download the first time (a few minutes)."
    if [ "$DRY" = 1 ]; then
        say "  plan: sudo apt-get update"
        say "  plan: sudo apt-get install -y cage chromium pipewire pipewire-pulse wireplumber"
        say "(dry run - nothing was changed)"
        return
    fi
    as_root env DEBIAN_FRONTEND=noninteractive apt-get update
    # Debian calls the browser chromium; some Pi images call it chromium-browser.
    if apt-cache show chromium >/dev/null 2>&1; then
        as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y cage chromium pipewire pipewire-pulse wireplumber
    else
        as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y cage chromium-browser pipewire pipewire-pulse wireplumber
    fi
    say "Installed. Run it from the Pi's own screen (not SSH):"
    say "  sh tubewing.sh run        (or from the Pi App Store)"
}

cmd_run() {
    URL=$URL_MAIN
    [ "${1:-}" = "--tv" ] && URL=$URL_TV
    BROWSER=$(command -v chromium || command -v chromium-browser || true)
    if [ "$DRY" = 1 ] && [ -z "$BROWSER" ]; then BROWSER=chromium; fi
    if [ -z "$BROWSER" ]; then
        say "Chromium is not installed yet. Run: sh tubewing.sh install" >&2
        exit 1
    fi
    if [ "$DRY" != 1 ] && ! command -v cage >/dev/null 2>&1; then
        say "cage is not installed yet. Run: sh tubewing.sh install" >&2
        exit 1
    fi
    if [ -n "${SSH_CONNECTION:-}" ] || [ -n "${SSH_TTY:-}" ]; then
        say "You are on SSH. tubewing draws on the Pi's own screen, so run it there."
        say "On the Pi: sh tubewing.sh run"
        exit 1
    fi
    say "Starting tubewing ($URL)"
    say "Leave: press Ctrl+Q, or switch to the console with Ctrl+Alt+F1."
    [ "$DRY" = 1 ] && { say "  plan: pipewire + wireplumber + pipewire-pulse (background)"; say "  plan: exec cage -s -- $BROWSER --kiosk ... $URL"; say "(dry run - nothing was started)"; return; }
    pipewire >/dev/null 2>&1 &
    sleep 1
    wireplumber >/dev/null 2>&1 &
    pipewire-pulse >/dev/null 2>&1 &
    exec cage -s -- "$BROWSER" \
        --kiosk --no-first-run --no-default-browser-check --noerrdialogs \
        --autoplay-policy=no-user-gesture-required \
        --disable-session-crashed-bubble --hide-crash-restore-bubble \
        "$URL"
}

cmd_uninstall() {
    say "tubewing - uninstall"
    say "Removing the mini desktop packages (your files and other apps stay)."
    if [ "$DRY" = 1 ]; then
        say "  plan: sudo apt-get remove --purge cage chromium pipewire-pulse wireplumber pipewire"
        say "(dry run - nothing was changed)"
        return
    fi
    as_root apt-get remove --purge -y cage chromium chromium-browser pipewire-pulse wireplumber pipewire 2>/dev/null || true
    as_root apt-get autoremove -y || true
    say "Done."
}

cmd_status() {
    say "tubewing $VERSION"
    if command -v cage >/dev/null 2>&1 && { command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; }; then
        say "installed: yes"
    else
        say "installed: no (run: sh tubewing.sh install)"
    fi
    say "run: sh tubewing.sh run  (full site)  |  sh tubewing.sh run --tv  (TV layout)"
}

case "${1:-status}" in
    install) cmd_install ;;
    run) shift || true; cmd_run "$@" ;;
    uninstall) cmd_uninstall ;;
    status) cmd_status ;;
    *) say "Use: sh tubewing.sh [--dry-run] install|run [--tv]|uninstall|status"; exit 1 ;;
esac
