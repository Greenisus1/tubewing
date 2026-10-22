# tubewing

A tiny kiosk desktop for watching YouTube on a console Home Pi (or any
Raspberry Pi OS Lite). One mini graphical session - the cage compositor plus
Chromium fullscreen - with no desktop environment to install or manage.

Built with AI assistance from my design.

- Its own "desktop": a dedicated full-screen session, separate from the
  console. No HomeOS Plus or PIXEL needed - this is for the normal Home Pi.
- Zero setup: `install` pulls the packages, `run` starts watching.
- Sound works on Lite (pipewire is set up for you).
- Leaving is safe: press Ctrl+Q (or Ctrl+Alt+F1 for the console). Closing the
  browser ends the session and you land back on your console.

## Use

From the Pi App Store (Apps section), or by hand on the Pi's own screen:

```sh
bash app-store.sh install    # one time
bash app-store.sh run        # full YouTube site
sh tubewing.sh run --tv      # YouTube's TV layout instead
```

Run it on the Pi's own screen. Over SSH it will refuse and tell you - the
session draws on the Pi's display.

## Honest notes

- First install downloads a few hundred MB (Chromium is big).
- Pi 5 plays smoothly. A Pi 3A+ can run it but expect choppy HD; 480p is fine.
- YouTube is a Google product; tubewing just opens it in a browser.
  Sign-in, ads, and availability are YouTube's own behavior.
- Needs the Pi's official OS (or Debian Trixie) on arm64 or armv7l.

MIT license. "YouTube" is a trademark of Google; tubewing is an independent
app and not affiliated with or endorsed by Google.
