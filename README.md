# Lumen

**Lumen** is a modular, open-source Discord bot built with **Python 3** and **SQLite3**, designed for creators, freelancers, and communities who need a secure, data-driven solution to collect feedback, detect scams, and automate routine moderation tasks.

<details>
<summary>📑 Table of Contents</summary>

1. [Overview](#1-overview)
2. [Key Features](#2-key-features)
3. [Architecture & Design](#3-architecture--design)
4. [Safety & Security](#4-safety--security)
5. [Installation & Setup](#5-installation--setup)
6. [Configuration Checklist](#6-configuration-checklist)
7. [Usage Notes & Limitations](#7-usage-notes--limitations)
8. [Contributing](#8-contributing)
9. [License](#9-license)
10. [Author & Links](#10-author--links)
</details>

---

## 1 – Overview

Lumen is **not** a drop‑in, invite‑and‑forget bot. It’s a back‑end toolkit that assumes familiarity with Python and server management. Designed for extensibility and customization, Lumen helps you:

- **Collect** structured feedback via slash commands and interactive panels
- **Detect** and filter out fake feedback, spam, and phishing attempts
- **Manage** premium access, user blacklists, and keyword filters with minimal fuss

Whether you’re running a small community or a large server network, Lumen gives you the building blocks to maintain order and gather insights without compromising on security.

---

## 2 – Key Features

| Module                     | Capabilities                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| **Feedback Suite**         | • `/feedback` slash command
                              • Interactive web‑style panels
                              • Duplicate and copy‑pasta detection
                              
| **Scam & Spam Filters**    | • Invite‑link blacklist
                              • Role & user blacklist
                              • Regex‑based keyword filters
                              |
| **Premium Manager**        | • Semi‑automatic state handling
                              • Expiry & renewal commands
                              • Manual override options
                              |
| **Reporting**              | • Automated monthly CSV & JSON summaries
                              • Audit logs per command (rotateable)
                              |
| **Security Utilities**     | • Bcrypt‑hashed credentials
                              • OTP password resets via Discord DM
                              • Rate limits & cooldown decorators
                              |

---

## 3 – Architecture & Design

Lumen’s codebase is organized into loosely coupled modules. Key packages include:

- **`bot/`** – Entry point & event loop (`main.py`)
- **`cogs/`** – Command sets, separated by function (feedback, moderation, premium)
- **`utils/`** – Shared utilities (rate limiting, hashing, DB interfaces)
- **`db/`** – SQLite schema migrations & upgrade scripts

> **Tip:** Use `python tools/db_upgrade.py` when schema changes are introduced. Always back up `lumen.db` before running migrations.

---

## 4 – Safety & Security

- **Transport Security**: All HTTP communication uses `aiohttp` w/ TLS 1.2+.
- **Data Encryption**: Credentials hashed with **bcrypt**; adjustable work factor.
- **Access Control**: Default scopes limited to `bot` and `applications.commands`.
- **Audit Logs**: Rotateable, per-command logs stored locally.
- **GDPR Compliance**: Minimal data collection; no external analytics.

> **Note:** Regularly rotate admin passwords and audit your `.env` for exposed secrets.

---

## 5 – Installation & Setup

1. **Clone & Install**
   ```bash
   git clone https://github.com/kimsuvo/lumen.git
   cd lumen
   pip install -r requirements.txt  # Python 3.11+
   ```

2. **Environment**
   ```bash
   cp example.env .env
   # Edit .env: BOT_TOKEN, TOPGG_TOKEN, BOT_ID, BOT_INFO_PASSWORD, DELETION_PASSWORD
   ```

3. **Initial Database**
   ```bash
   python tools/db_upgrade.py
   ```

4. **Run**
   ```bash
   python main.py
   ```

---

## 6 – Configuration Checklist

- [ ] **Environment Variables**
  - `BOT_TOKEN`, `TOPGG_TOKEN`, `BOT_ID`
  - `BOT_INFO_PASSWORD`, `DELETION_PASSWORD`
- [ ] **IDs & Constants**
  - Verify `config.py` values: guild, channel, category, role IDs
- [ ] **Security Settings**
  - Set `BCRYPT_WORK_FACTOR`, OTP expiry, rate limits
- [ ] **Branding & UX**
  - Update `embeds.py` for colors, thumbnails, footers
- [ ] **Permissions**
  - Ensure each role in `config.ROLES` exists and has bot permissions
- [ ] **Housekeeping**
  - Remove sample data files (`test.txt`, mock CSVs)

---

## 7 – Usage Notes & Limitations

- **Active Development:** Breaking changes may occur; pin versions or branch off.
- **SQLite Limits:** >1 req/sec can lock; consider MySQL/Postgres for high throughput.
- **Slash Command Sync:** Throttling on >100 servers; stagger syncs if needed.
- **Verbose Logging:** Logs are chatty by design—consult them before opening issues.

---

## 8 – Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/XYZ`)
3. Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) and write type hints + docstrings
4. Write unit tests for new commands (`/tests`)
5. Open a PR & tag reviewers

For security issues, please allow a 7-day acknowledgment window and 30-day fix window before public disclosure.

---

## 9 – License

Lumen is released under the [MIT License](./LICENSE). You are free to use, modify, and distribute with attribution.

---

## 10 – Author & Links

**Kim Suvo**

- GitHub: [kimsuvo](https://github.com/kimsuvo)

