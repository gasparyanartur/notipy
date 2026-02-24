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

**1. Choose your address and set it**

Pick any unique string as your address (e.g. your name, a random token). Add it to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export NOTIPY_ADDR="yourname-abc123"' >> ~/.bashrc
source ~/.bashrc
```

Or put it in a per-project `.env` file (see [Environment variables](#environment-variables) for how to load it).

**2. Subscribe to your topic**

Your ntfy topic is `notipy-<your-addr>`. Install the [ntfy app](https://ntfy.sh/#subscribe-phone) (Android / iOS / web) and subscribe to:

```
notipy-yourname-abc123
```

Or open it in a browser: `https://ntfy.sh/notipy-yourname-abc123`

**3. Run anything**

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
| `--addr / -a ADDR` | Address suffix; the ntfy topic becomes `notipy-<addr>` (overrides `NOTIPY_ADDR`) |
| `--no-notify` | Run the command but skip sending the notification |

### Examples

```bash
# Use a private address
notipy --addr my-secret-abc123 -- make build

# Override via env var
export NOTIPY_ADDR="my-secret-abc123"
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
| `NOTIPY_ADDR` | `gasparyanartur-public` | Address suffix used to build the ntfy topic `notipy-<addr>` |

### Setting `NOTIPY_ADDR`

**Option 1 — `~/.bashrc` / `~/.zshrc`** (persists for all shell sessions):

```bash
echo 'export NOTIPY_ADDR="my-secret-abc123"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2 — `.env` file** (per-project, load with a tool like [`dotenv`](https://github.com/theskumar/python-dotenv) or [`direnv`](https://direnv.net/)):

```bash
# .env
NOTIPY_ADDR=my-secret-abc123
```

Then load it before running notipy:

```bash
# with direnv (auto-loads .env when you cd into the directory)
direnv allow

# or manually
set -a && source .env && set +a
notipy -- python train.py
```

Pick a sufficiently unique string as your address — topic names are the only form of access control on the public ntfy.sh server.  
For full privacy you can [self-host ntfy](https://docs.ntfy.sh/install/).

---

## How it works

1. `notipy` launches your command in a shell via `subprocess.Popen`.
2. stdout and stderr are **tee'd** — forwarded to your terminal in real time *and* captured concurrently using two daemon threads.
3. After the process exits, a plain-text notification is `POST`ed to `https://ntfy.sh/` (with the topic embedded in the JSON body) using Python's built-in `http.client` (zero external dependencies).
4. `notipy` exits with the **same exit code** as the wrapped command.

---

## License

MIT
