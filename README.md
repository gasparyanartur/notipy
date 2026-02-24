# notipy

> Wrap any shell command and get a **push notification** when it finishes.

```bash
notipy -- python train.py --epochs 100
```

When the command completes you receive a push notification on your phone / browser with:
- Title: `✅ 'python train.py --epochs 100' done` (or ❌ failed)
- Body: hostname, full stdout + stderr (truncated at 4 KB if needed)

**No account. No credentials. No setup.**  
Notifications are delivered by [ntfy.sh](https://ntfy.sh), a free open-source push notification service.

---

## Installation

### pip (from GitHub)

```bash
pip install git+https://github.com/<you>/notipy.git
```

### Editable / development install

```bash
git clone https://github.com/<you>/notipy.git
cd notipy
pip install -e .
```

After installation the `notipy` command is available globally.

---

## Quick start

**1. Subscribe to the notipy topic**

Install the [ntfy app](https://ntfy.sh/#subscribe-phone) (Android / iOS / web) and subscribe to the topic:

```
gasparyanartur-notipy-public
```

Or open it in a browser: https://ntfy.sh/gasparyanartur-notipy-public

**2. Run anything**

```bash
notipy -- sleep 10
notipy -- python train.py --epochs 100
```

That's it.

---

## Usage

```
notipy [OPTIONS] -- COMMAND [ARGS…]
```

| Option | Description |
|---|---|
| `--topic / -t TOPIC` | ntfy.sh topic (overrides `NOTIPY_TOPIC`, default: `gasparyanartur-notipy-public`) |
| `--no-notify` | Run the command but skip sending the notification |

### Examples

```bash
# Use a private topic
notipy --topic my-secret-topic-abc123 -- make build

# Override via env var
export NOTIPY_TOPIC="my-secret-topic-abc123"
notipy -- python train.py

# Test without notifying
notipy --no-notify -- echo hello

# Arguments that look like flags are safe after --
notipy -- python train.py --lr 0.001 --epochs 50
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `NOTIPY_TOPIC` | `gasparyanartur-notipy-public` | ntfy.sh topic to publish to |

To use a private topic, set it in `~/.bashrc` or `~/.zshrc`:

```bash
export NOTIPY_TOPIC="my-secret-topic-abc123"
```

Pick any long random string — topic names are the only form of access control on the public ntfy.sh server.  
For full privacy you can [self-host ntfy](https://docs.ntfy.sh/install/).

---

## How it works

1. `notipy` launches your command in a shell via `subprocess.Popen`.
2. stdout and stderr are **tee'd** — forwarded to your terminal in real time *and* captured concurrently using two daemon threads.
3. After the process exits, a plain-text notification is `POST`ed to `https://ntfy.sh/<topic>` using Python's built-in `urllib` (zero external dependencies).
4. `notipy` exits with the **same exit code** as the wrapped command.

---

## License

MIT
