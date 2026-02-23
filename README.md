# notipy

> Wrap any shell command and get an **email notification with logs** when it finishes.

```
notipy -- python train.py --epochs 100
```

When the command completes you receive an email with:
- Subject: `notipy: 'python train.py --epochs 100' ✅ done`  (or ❌ failed)
- Body: host, command, exit status
- Attachment: `logs.txt` — full stdout + stderr

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

```bash
# 1. Set SMTP credentials (see "SMTP setup" below)
export NOTIPY_SMTP_USER="you@gmail.com"
export NOTIPY_SMTP_PASS="your-app-password"

# 2. Set the default recipient
export NOTIPY_EMAIL_ADDR="you@example.com"

# 3. Run something
notipy -- sleep 10
```

---

## Usage

```
notipy [OPTIONS] -- COMMAND [ARGS…]
```

| Option | Description |
|---|---|
| `--to / -t ADDRESS` | Recipient address (overrides `NOTIPY_EMAIL_ADDR`) |
| `--subject / -s TEXT` | Custom email subject (auto-generated if omitted) |
| `--no-mail` | Run the command but skip sending the email |

### Examples

```bash
# Use --to to override the env-var recipient
notipy --to boss@company.com -- make build

# Custom subject
notipy --subject "Training run done" -- python train.py

# Test without sending mail
notipy --no-mail -- echo hello

# Arguments that look like flags are safe after --
notipy -- python train.py --lr 0.001 --epochs 50
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `NOTIPY_EMAIL_ADDR` | ✅ (or `--to`) | — | Recipient email address |
| `NOTIPY_SMTP_USER` | ✅ | — | SMTP login username (also the sender) |
| `NOTIPY_SMTP_PASS` | ✅ | — | SMTP password or app-password |
| `NOTIPY_SMTP_HOST` | ❌ | `smtp.gmail.com` | SMTP server hostname |
| `NOTIPY_SMTP_PORT` | ❌ | `587` | SMTP port (STARTTLS) |
| `NOTIPY_FROM_ADDR` | ❌ | `NOTIPY_SMTP_USER` | Override the From address |

Add these to your `~/.bashrc` or `~/.zshrc` to make them permanent:

```bash
export NOTIPY_SMTP_USER="you@gmail.com"
export NOTIPY_SMTP_PASS="xxxx xxxx xxxx xxxx"   # app password
export NOTIPY_EMAIL_ADDR="you@example.com"
```

---

## SMTP setup

### Gmail (recommended)

Gmail requires an **App Password** when 2-Step Verification is enabled (regular passwords won't work).

1. Go to **Google Account → Security → 2-Step Verification** and enable it.
2. Go to **Google Account → Security → App passwords**.
3. Select app: *Mail*, device: *Other (custom name)*, enter `notipy`.
4. Copy the 16-character password and set `NOTIPY_SMTP_PASS` to it.

```bash
export NOTIPY_SMTP_USER="you@gmail.com"
export NOTIPY_SMTP_PASS="abcd efgh ijkl mnop"
```

### Other providers

| Provider | `NOTIPY_SMTP_HOST` | `NOTIPY_SMTP_PORT` |
|---|---|---|
| Gmail | `smtp.gmail.com` | `587` |
| Outlook / Hotmail | `smtp-mail.outlook.com` | `587` |
| Yahoo Mail | `smtp.mail.yahoo.com` | `587` |
| Fastmail | `smtp.fastmail.com` | `587` |
| SendGrid | `smtp.sendgrid.net` | `587` |
| Custom / self-hosted | your server | `587` |

---

## How it works

1. `notipy` launches your command in a bash shell via `subprocess.Popen`.
2. stdout and stderr are **tee'd** — forwarded to your terminal in real time *and* captured concurrently using two daemon threads.
3. After the process exits, a MIME email is built:
   - Plain-text body with host, command, and exit status.
   - `logs.txt` attachment containing full stdout + stderr.
4. The email is sent over STARTTLS SMTP and `notipy` exits with the **same exit code** as the wrapped command.

---

## License

MIT
