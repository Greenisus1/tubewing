#!/bin/sh
# pi-app-store: 1
# pi-app-store-category: apps
set -eu
cd -- "$(dirname -- "$0")"
case "${1:-run}" in
    install) sh tubewing.sh install ;;
    uninstall) sh tubewing.sh uninstall ;;
    run) shift || true; sh tubewing.sh run "$@" ;;
    *) echo 'Use: bash app-store.sh install | uninstall | run'; exit 1 ;;
esac
