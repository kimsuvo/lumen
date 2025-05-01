# lumen
Lumen is a powerful open-source Discord bot built with Python and SQLite3, designed to collect feedback, detect scams, and automate moderation.

A modular, open-source Discord bot built with Python 3 + SQLite 3.  
Created for creators, freelancers, and communities who need a secure, data-driven way to collect feedback, spot scams, and automate routine moderation.

--------------------------------------------------------------------------------
Table of Contents
--------------------------------------------------------------------------------
1. Overview
2. Features
3. Safety & Security
4. Installation
5. Configuration Checklist
6. Usage Notes & Limitations
7. Contributing & Responsible Disclosure
8. License
9. Author & Links
--------------------------------------------------------------------------------

## 1 – Overview
Lumen is **not** a one-click “invite & forget” bot.  
It is a back-end toolkit that assumes you are comfortable reading and editing Python.  
Expect to tweak multiple files before production deployment.

## 2 – Features
- **Feedback Collection** – Slash-command & panel-based UX for structured reviews.
- **Fake-Feedback Detection** – Heuristics against copy-pasta, duplicate IP / device IDs (optional), throw-away accounts, and mass-DM adverts.
- **Blacklist Suite**  
  • Invite-link blacklist  
  • User & role blacklist  
  • Keyword / regex filters for scams or phishing  
- **Premium Manager (Semi-Auto)** – Per-guild premium state with expiry, auto-revoke, and manual override commands.  
- **Monthly Reports** – Auto-generate CSV / JSON summaries for admins.  
- **Storage & Encryption**  
  • SQLite 3 for local persistence  
  • All user credentials hashed with **bcrypt**  
  • Per-command audit logs (rotateable)  
- **OTP Password Reset** – Six-digit, time-bound codes delivered via Discord DM for forgotten passwords.  
- **Rate-Limiting & Cool-Downs** – Built-in decorator utilities to mitigate spam and brute-force OTP attempts.

## 3 – Safety & Security
- **Transport Security** – All outbound HTTP uses `aiohttp` with TLS 1.2+.  
- **Hashing** – Passwords and sensitive tokens hashed with `bcrypt` (configurable work factor).  
- **Data Scope** – Lumen stores data **only** on your server unless you add external sync.  
- **Permission Hardening** – The default bot token requires `bot + applications.commands`. No admin scope is requested unless you grant it.  
- **Back-Up Strategy** – SQLite is file-based; schedule off-disk backups and test restore procedures.  
- **GDPR / Privacy** – The bot collects the minimal data needed for functionality. No analytics or tracking are shipped.  
- **Discord Compliance** – Usage must follow:  
  • Discord Terms of Service <https://discord.com/tos>  
  • Discord Community Guidelines <https://discord.com/guidelines>  

> **Disclaimer**  
> Violating Discord policies with this code is solely your responsibility. The repository maintainers disclaim all liability for misuse, data loss, or damages.

## 4 – Installation
```sh
git clone https://github.com/kimsuvo/lumen.git
cd lumen-bot
pip install -r requirements.txt      # Python 3.11+ recommended
cp example.env .env                  # then edit .env with your secrets
python main.py
```
## 5 – Configuration Checklist
- [ ] **Environment:**  
      Create a `.env` file (or set host-level secrets) with:  
      `BOT_TOKEN`, `TOPGG_TOKEN`, `BOT_ID`, `BOT_INFO_PASSWORD`, `DELETION_PASSWORD`.
- [ ] **IDs & Constants:**  
      Open `config.py` and verify every guild, role, category, and channel ID matches your server.
- [ ] **Security Parameters:**  
      • Adjust `BCRYPT_WORK_FACTOR`, OTP length / expiry, and rate-limit values to suit your risk profile.  
      • Rotate the two admin passwords before going live.
- [ ] **Branding & UX:**  
      Edit `embeds.py` (or your equivalent view layer) to set colours, thumbnails, and footer text for your brand.
- [ ] **Staff Permissions:**  
      Ensure every staff / moderator role listed in `config.ROLES` actually exists on Discord and has the right bot permissions.
- [ ] **Database:**  
      Run `python tools/db_upgrade.py` once if you altered the schema; back up `lumen.db` before production.
- [ ] **Housekeeping:**  
      Delete sample data (`test.txt`, mock CSVs, etc.) from any module or resource folder.

## 6 – Usage Notes & Limitations
* The repository is **under active development**; expect breaking changes.  
* Some modules use experimental slash-command sync that may throttle on large guilds.  
* Heavy write workloads (> 1 req / sec) can lock SQLite; migrate to MySQL or Postgres if needed.  
* Error handling is verbose by design—read the logs before opening an issue.

## 7 – Contributing & Responsible Disclosure
Bug reports and pull requests are welcome. For security issues, please:  

2. Allow 7 days for acknowledgement and 30 days for a public fix before disclosure.  

### Development Guidelines
- Follow PEP 8.
- Write type hints (`typing` module) and docstrings.
- Each new command must include unit tests in `/tests`.

## 8 – License
This project is released under the **MIT License**.  
You may use, distribute, and modify with attribution.  
See `LICENSE` in the repo root.

## 9 – Author & Links
Created by **Kim Suvo**  
• GitHub: <https://github.com/kimsuvo>  
