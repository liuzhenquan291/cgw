#!/usr/bin/env python3
"""cgw - Claude Gateway command line tool.

Usage:
    cgw status              Show gateway and profile status
    cgw profiles            List all profiles
    cgw active              Show active profile
    cgw switch <name>       Switch to a profile
    cgw add                 Add a new profile (interactive)
    cgw edit <name>         Edit a profile
    cgw remove <name>       Remove a profile
    cgw start               Start the gateway
    cgw stop                Stop the gateway
    cgw restart             Restart the gateway
    cgw web                 Open the web admin page
    cgw logs                View gateway logs
    cgw install             Install cgw to PATH
"""

import json
import os
import signal
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, "gateway.pid")
LOG_FILE = os.path.join(BASE_DIR, "gateway.log")
ENV_FILE = os.path.join(BASE_DIR, ".env")
ADMIN_URL = "http://127.0.0.1:8787/admin"

sys.path.insert(0, BASE_DIR)
from profile_manager import ProfileManager


def color(text, c):
    codes = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
             "blue": "\033[34m", "cyan": "\033[36m", "gray": "\033[90m",
             "bold": "\033[1m", "reset": "\033[0m"}
    return codes.get(c, "") + text + codes["reset"]


def safe_input(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(1)


def get_pid():
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        # Verify it's actually a Python/uvicorn process, not a recycled PID
        try:
            import subprocess
            out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "comm="],
                stderr=subprocess.DEVNULL,
            )
            comm = out.decode().strip()
            if "python" not in comm.lower() and "uvicorn" not in comm.lower():
                return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return pid
    except (OSError, ValueError):
        return None


def is_running():
    return get_pid() is not None


def load_env_key():
    if not os.path.exists(ENV_FILE):
        return ""
    with open(ENV_FILE) as f:
        for line in f:
            if line.strip().startswith("MIMO_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def write_env_key(key):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if not line.strip().startswith("MIMO_API_KEY="):
                    lines.append(line.rstrip("\n"))
    lines.append("MIMO_API_KEY={}".format(key))
    tmp = ENV_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, ENV_FILE)


# ── commands ────────────────────────────────────────────


def cmd_status():
    pm = ProfileManager()
    data = pm.list_profiles()
    active = data["active"]
    profiles = data["profiles"]

    print(color("  Claude Gateway Status", "bold"))
    print()

    if is_running():
        print("  Gateway:    " + color("● Running", "green") + " (PID: {})".format(get_pid()))
    else:
        print("  Gateway:    " + color("● Stopped", "red"))

    if active and active in profiles:
        p = profiles[active]
        print("  Profile:    " + color("● " + active, "cyan"))
        print("  Upstream:   " + p.get("upstream_url", "-"))
        print("  API Key:    " + (p.get("api_key", "")[:8] + "..." if p.get("api_key") else "-"))
        print("  Models:     {}".format(len(p.get("models", []))))
    else:
        print("  Profile:    " + color("● Not configured", "yellow"))

    print("  Config:     ~/.claude-gateway/profiles.json")
    print()

    if not is_running():
        print("  Start: " + color("cgw start", "cyan"))
    if not active:
        print("  Setup: " + color("cgw add", "cyan"))


def cmd_profiles():
    pm = ProfileManager()
    data = pm.list_profiles()
    active = data["active"]
    profiles = data["profiles"]

    if not profiles:
        print(color("  No profiles configured", "yellow"))
        print("  Run " + color("cgw add", "cyan") + " to create your first profile")
        return

    print(color("  All Profiles", "bold"))
    print()
    for name, p in sorted(profiles.items()):
        marker = "●" if name == active else "○"
        c = "green" if name == active else "gray"
        models = p.get("models", [])
        print("  {} {}  ({} models)".format(
            color(marker, c), color(name, "bold" if name == active else ""), len(models)))
        print("    {}".format(p.get("upstream_url", "-")))
    print()


def cmd_active():
    pm = ProfileManager()
    p = pm.get_active_profile()
    if not p:
        print(color("  No active profile", "yellow"))
        return
    print(color("  Active Profile: " + p["name"], "bold"))
    print()
    print("  Upstream:   {}".format(p.get("upstream_url", "-")))
    print("  Auth:       {}".format(p.get("auth_scheme", "api-key")))
    print("  API Key:    {}".format(p.get("api_key", "")[:8] + "..." if p.get("api_key") else "-"))
    print("  Models:")
    for m in p.get("models", []):
        print("    {} -> {}  ({})".format(m["id"], m["upstream"], m.get("display_name", m["id"])))


def cmd_switch(name):
    pm = ProfileManager()
    try:
        p = pm.switch_profile(name)
        print(color("  OK: Switched to profile: " + name, "green"))
        print("    Upstream: {}".format(p.get("upstream_url", "-")))
        print()
        print(color("  Changes take effect on next request.", "yellow"))
        print("    " + color("cgw restart", "cyan"))
    except KeyError as e:
        print(color("  Error: " + str(e), "red"))
        print("  Run " + color("cgw profiles", "cyan") + " to see available profiles")


def cmd_add():
    print(color("  Create New Profile", "bold"))
    print()

    name = safe_input("  Profile name: ").strip()
    if not name:
        print(color("  Error: Name cannot be empty", "red"))
        return

    url = safe_input("  Upstream URL: ").strip()
    if not url:
        print(color("  Error: URL cannot be empty", "red"))
        return

    key = safe_input("  API Key: ").strip()
    if not key:
        print(color("  Error: API Key cannot be empty", "red"))
        return

    auth = safe_input("  Auth scheme (api-key/x-api-key/Authorization) [api-key]: ").strip() or "api-key"

    print()
    print("  Add model mappings (enter empty line to finish):")
    models = []
    while True:
        mid = safe_input("    Claude Model ID: ").strip()
        if not mid:
            break
        upstream = safe_input("    Upstream Model: ").strip()
        if not upstream:
            print(color("    Error: Upstream cannot be empty", "red"))
            continue
        display = safe_input("    Display name [{}]: ".format(mid)).strip() or mid
        models.append({"id": mid, "upstream": upstream, "display_name": display})
        print()

    pm = ProfileManager()
    try:
        pm.add_profile(name, url, key, models, auth)
        write_env_key(key)
        print(color("  OK: Profile created: " + name, "green"))
        print()
        print(color("  Changes take effect on next request.", "yellow"))
        print("    " + color("cgw restart", "cyan"))
    except (ValueError, KeyError) as e:
        print(color("  Error: " + str(e), "red"))


def cmd_edit(name):
    pm = ProfileManager()
    p = pm.get_profile(name)
    if not p:
        print(color("  Error: Profile not found: " + name, "red"))
        return

    print(color("  Edit Profile: " + name, "bold"))
    print()

    url = safe_input("  Upstream URL [{}]: ".format(p.get("upstream_url", ""))).strip()
    key = safe_input("  API Key [{}]: ".format(p.get("api_key", "")[:8] + "...")).strip()
    auth = safe_input("  Auth scheme [{}]: ".format(p.get("auth_scheme", "api-key"))).strip()

    try:
        pm.update_profile(
            name,
            upstream_url=url or None,
            api_key=key or None,
            auth_scheme=auth or None,
        )
        if key:
            write_env_key(key)
        print(color("  OK: Profile updated", "green"))
        print()
        print(color("  Changes take effect on next request.", "yellow"))
        print("    " + color("cgw restart", "cyan"))
    except (ValueError, KeyError) as e:
        print(color("  Error: " + str(e), "red"))


def cmd_remove(name):
    confirm = safe_input("  Delete profile '{}'? (y/N): ".format(name)).strip().lower()
    if confirm != "y":
        print("  Cancelled")
        return
    pm = ProfileManager()
    try:
        pm.delete_profile(name)
        print(color("  OK: Profile deleted: " + name, "green"))
    except KeyError as e:
        print(color("  Error: " + str(e), "red"))


def cmd_start():
    if is_running():
        print("  Gateway already running (PID: {})".format(get_pid()))
        return

    env_key = load_env_key()
    if not env_key:
        pm = ProfileManager()
        p = pm.get_active_profile()
        if p:
            env_key = p.get("api_key", "")
            write_env_key(env_key)

    env = os.environ.copy()
    if env_key:
        env["MIMO_API_KEY"] = env_key

    with open(LOG_FILE, "a") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "gateway:app",
             "--host", "127.0.0.1", "--port", "8787"],
            stdout=log, stderr=log,
            cwd=BASE_DIR, env=env,
        )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    import time
    time.sleep(2)
    if is_running():
        print(color("  OK: Gateway started (PID: {})".format(proc.pid), "green"))
        print("  Admin page: " + color(ADMIN_URL, "cyan"))
    else:
        print(color("  Error: Startup failed. Check logs: cgw logs", "red"))


def kill_port(port):
    """Kill all processes listening on the given port."""
    try:
        out = subprocess.check_output(
            ["lsof", "-ti", ":{}".format(port)],
            stderr=subprocess.DEVNULL,
        )
        pids = [int(p) for p in out.strip().split(b"\n") if p]
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        return pids
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def cmd_stop():
    pid = get_pid()
    killed = []
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
            import time
            time.sleep(0.5)
        except (ProcessLookupError, PermissionError):
            pass

    # Kill any remaining processes on the gateway port
    port_killed = kill_port(8787)
    killed.extend(port_killed)

    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    if killed:
        print(color("  OK: Gateway stopped (killed PIDs: {})".format(killed), "green"))
    else:
        print("  Gateway is not running")


def cmd_restart():
    cmd_stop()
    import time
    time.sleep(1)
    cmd_start()


def cmd_web():
    print("  Opening admin page: " + color(ADMIN_URL, "cyan"))
    try:
        subprocess.Popen(["open", ADMIN_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("  Please open manually in your browser: " + ADMIN_URL)


def cmd_logs():
    if not os.path.exists(LOG_FILE):
        print("  Log file not found")
        return
    os.execvp("tail", ["tail", "-f", LOG_FILE])


def cmd_install():
    bin_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(bin_dir, exist_ok=True)
    link_path = os.path.join(bin_dir, "cgw")
    script = os.path.join(BASE_DIR, "cli.py")

    content = "#!/usr/bin/env bash\nexec {} {} \"$@\"\n".format(sys.executable, script)
    with open(link_path, "w") as f:
        f.write(content)
    os.chmod(link_path, 0o755)

    print(color("  OK: cgw installed to " + link_path, "green"))
    print()
    shell_rc = os.path.expanduser("~/.zshrc")
    path_line = 'export PATH="$HOME/.local/bin:$PATH"'

    if os.path.exists(shell_rc):
        with open(shell_rc) as f:
            if path_line not in f.read():
                with open(shell_rc, "a") as f2:
                    f2.write("\n# Claude Gateway\n" + path_line + "\n")
                print(color("  OK: PATH added to ~/.zshrc", "green"))
                print("  Please run: " + color("source ~/.zshrc", "cyan"))
            else:
                print("  PATH already configured")
    else:
        print("  Please add ~/.local/bin to your PATH manually")


# ── main ────────────────────────────────────────────────


def main():
    args = sys.argv[1:]

    if not args:
        cmd_status()
        return

    cmd = args[0]

    if cmd == "status":
        cmd_status()
    elif cmd == "profiles" or cmd == "ls":
        cmd_profiles()
    elif cmd == "active":
        cmd_active()
    elif cmd == "switch" or cmd == "use":
        if len(args) < 2:
            print(color("  Usage: cgw switch <name>", "red"))
            return
        cmd_switch(args[1])
    elif cmd == "add" or cmd == "new":
        cmd_add()
    elif cmd == "edit":
        if len(args) < 2:
            print(color("  Usage: cgw edit <name>", "red"))
            return
        cmd_edit(args[1])
    elif cmd == "remove" or cmd == "rm":
        if len(args) < 2:
            print(color("  Usage: cgw remove <name>", "red"))
            return
        cmd_remove(args[1])
    elif cmd == "start" or cmd == "up":
        cmd_start()
    elif cmd == "stop" or cmd == "down":
        cmd_stop()
    elif cmd == "restart":
        cmd_restart()
    elif cmd == "web":
        cmd_web()
    elif cmd == "logs":
        cmd_logs()
    elif cmd == "install":
        cmd_install()
    elif cmd == "help" or cmd == "--help" or cmd == "-h":
        print(__doc__)
    else:
        print(color("  Unknown command: " + cmd, "red"))
        print("  Run " + color("cgw help", "cyan") + " for usage information")


if __name__ == "__main__":
    main()
