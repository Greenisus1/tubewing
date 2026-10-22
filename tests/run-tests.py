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


# --- first-launch input wizard -----------------------------------------
import tempfile
THOME = tempfile.mkdtemp(prefix="tubewing-test-")

r = subprocess.run(["sh", os.path.join(ROOT, "tubewing.sh"), "setup"],
                   input="2\n", capture_output=True, text=True,
                   env={**os.environ, "TUBEWING_HOME": THOME})
check("setup prints the three choices",
      "Mouse" in r.stdout and "Keyboard" in r.stdout and "Touchpad" in r.stdout)

r = subprocess.run(["sh", os.path.join(ROOT, "tubewing.sh"), "setup"],
                   input="2\n", capture_output=True, text=True,
                   env={**os.environ, "TUBEWING_HOME": THOME,
                        "SSH_CONNECTION": "", "SSH_TTY": ""})
check("choosing 2 saves keyboard", "Saved: keyboard" in r.stdout)
cfg = open(os.path.join(THOME, "tubewing", "config")).read()
check("config file remembers keyboard", cfg.strip() == "input=keyboard")

r = subprocess.run(["sh", os.path.join(ROOT, "tubewing.sh"), "setup"],
                   input="3\n", capture_output=True, text=True,
                   env={**os.environ, "TUBEWING_HOME": THOME})
check("choosing 3 saves touchpad", "Saved: touchpad" in r.stdout)

r = subprocess.run(["sh", os.path.join(ROOT, "tubewing.sh"), "setup"],
                   input="\n", capture_output=True, text=True,
                   env={**os.environ, "TUBEWING_HOME": THOME})
check("empty answer defaults to mouse", "Saved: mouse" in r.stdout)

rc, out = sh(["--dry-run", "run"], env_extra={"TUBEWING_HOME": THOME,
                                              "PATH": "/usr/bin:/bin"})
check("remembered input used (no re-ask)", "Pointer mode (mouse)" in out)

open(os.path.join(THOME, "tubewing", "config"), "w").write("input=keyboard\n")
rc, out = sh(["--dry-run", "run"], env_extra={"TUBEWING_HOME": THOME,
                                              "PATH": "/usr/bin:/bin"})
check("keyboard input selects TV layout", "Keyboard mode" in out
      and "youtube.com/tv" in out)
rc, out = sh(["--dry-run", "run", "--tv"], env_extra={"TUBEWING_HOME": THOME,
                                                      "PATH": "/usr/bin:/bin"})
check("explicit --tv still wins", "youtube.com/tv" in out)

rc, out = sh(["status"], env_extra={"TUBEWING_HOME": THOME})
check("status shows remembered input", "input: keyboard" in out)


def run_pty(argv, feed=None, env_extra=None, timeout=20):
    import select
    import time
    env = dict(os.environ)
    env.pop("SSH_CONNECTION", None)
    env.pop("SSH_TTY", None)
    if env_extra:
        env.update(env_extra)
    master, slave = pty.openpty()
    p = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave,
                         env=env, close_fds=True)
    os.close(slave)
    out = b""
    if feed is not None:
        time.sleep(0.5)
        os.write(master, feed)
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _w, _x = select.select([master], [], [], 0.5)
        if r:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
        elif p.poll() is not None:
            break
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    os.close(master)
    return out.decode("utf-8", "replace")


rc, out = sh(["--dry-run", "run"], env_extra={"PATH": "/usr/bin:/bin"})
check("browser runs Wayland-native (cage cannot host X11)",
      "--ozone-platform=wayland" in open(os.path.join(ROOT, "tubewing.sh")).read())
check("cursor theme is set for the session",
      "XCURSOR_THEME=Adwaita" in open(os.path.join(ROOT, "tubewing.sh")).read())
check("cursor theme package is installed",
      "adwaita-icon-theme" in open(os.path.join(ROOT, "tubewing.sh")).read())

txt = run_pty(["sh", os.path.join(ROOT, "tubewing.sh"), "--dry-run", "run"],
              env_extra={"PATH": "/usr/bin:/bin", "TUBEWING_HOME": THOME})
check("PTY: session plan renders in a terminal", "Starting tubewing" in txt
      and "--kiosk" in txt)

EMPTY_HOME = tempfile.mkdtemp(prefix="tubewing-first-")
txt = run_pty(["sh", os.path.join(ROOT, "tubewing.sh"), "--dry-run", "run"],
              feed=b"2\n",
              env_extra={"PATH": "/usr/bin:/bin", "TUBEWING_HOME": EMPTY_HOME})
check("PTY: first run asks the input question",
      "What will you use to control it?" in txt)
check("PTY: answering 2 plans keyboard save",
      "plan: save input=keyboard" in txt)
check("PTY: keyboard answer switches to TV layout plan",
      "Keyboard mode" in txt and "youtube.com/tv" in txt)

print()
if FAIL:
    print("%d FAILURES" % len(FAIL))
    sys.exit(1)
print("all tests passed")
