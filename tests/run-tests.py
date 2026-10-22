#!/usr/bin/env python3
"""tubewing tests: syntax, dry-run plans, SSH refusal, URL choices, PTY."""
import os
import pty
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FAIL = []


def check(name, cond):
    print(("ok  " if cond else "FAIL") + " " + name)
    if not cond:
        FAIL.append(name)


def sh(args, env_extra=None):
    env = dict(os.environ)
    env.pop("SSH_CONNECTION", None)
    env.pop("SSH_TTY", None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["sh", os.path.join(ROOT, "tubewing.sh")] + args,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


for f in ("tubewing.sh", "app-store.sh"):
    r = subprocess.run(["sh", "-n", os.path.join(ROOT, f)])
    check("syntax ok: %s" % f, r.returncode == 0)

rc, out = sh(["--dry-run", "install"])
check("dry-run install plans packages", "cage chromium pipewire" in out.replace("\\\n", " "))
check("dry-run install changes nothing", "nothing was changed" in out)

rc, out = sh(["--dry-run", "run"], env_extra={"PATH": "/usr/bin:/bin"})
check("dry-run run plans the session", "plan: exec cage" in out and "--kiosk" in out)
check("default URL is the full site", "https://www.youtube.com\n" in out or "youtube.com\n" in out)
check("exit hint printed", "Ctrl+Q" in out)

rc, out = sh(["--dry-run", "run", "--tv"], env_extra={"PATH": "/usr/bin:/bin"})
check("--tv uses the TV layout", "youtube.com/tv" in out)

rc, out = sh(["--dry-run", "run"], env_extra={"SSH_CONNECTION": "1 2 3 4"})
check("SSH run is refused with guidance", "on SSH" in out and rc == 1)

rc, out = sh(["status"])
check("status runs", "tubewing" in out)

rc, out = sh(["--dry-run", "uninstall"])
check("dry-run uninstall plans removal", "apt-get remove" in out)

rc, out = sh(["bogus"])
check("bad action prints usage", rc == 1 and "install|run" in out)


def run_pty(argv, env_extra=None):
    env = dict(os.environ)
    env.pop("SSH_CONNECTION", None)
    if env_extra:
        env.update(env_extra)
    out = []

    def read(fd):
        try:
            data = os.read(fd, 1024)
        except OSError:
            return b""
        out.append(data)
        return data

    old = dict(os.environ)
    os.environ.update(env)
    try:
        pty.spawn(argv, read)
    finally:
        os.environ.clear()
        os.environ.update(old)
    return b"".join(out).decode("utf-8", "replace")


rc, out = sh(["--dry-run", "run"], env_extra={"PATH": "/usr/bin:/bin"})
check("browser runs Wayland-native (cage cannot host X11)",
      "--ozone-platform=wayland" in open(os.path.join(ROOT, "tubewing.sh")).read())
check("cursor theme is set for the session",
      "XCURSOR_THEME=Adwaita" in open(os.path.join(ROOT, "tubewing.sh")).read())
check("cursor theme package is installed",
      "adwaita-icon-theme" in open(os.path.join(ROOT, "tubewing.sh")).read())

txt = run_pty(["sh", os.path.join(ROOT, "tubewing.sh"), "--dry-run", "run"],
              env_extra={"PATH": "/usr/bin:/bin"})
check("PTY: session plan renders in a terminal", "Starting tubewing" in txt
      and "--kiosk" in txt)

print()
if FAIL:
    print("%d FAILURES" % len(FAIL))
    sys.exit(1)
print("all tests passed")
