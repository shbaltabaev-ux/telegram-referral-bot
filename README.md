# Telegram Referral Bot

A minimal aiogram v3 bot that tracks referrals via personal invite links. Silent in groups; commands work only in private chat.

## .env configuration
Create a `.env` file with:

```
BOT_TOKEN=1234567890:ABC...
CHANNEL_ID=-1001234567890
ADMIN_IDS=123456789
DB_PATH=referrals.db
```

- BOT_TOKEN: from @BotFather
- CHANNEL_ID: your group ID (e.g., -100..., you can get it from @myidbot)
- ADMIN_IDS: your Telegram user ID(s), comma-separated if multiple
- DB_PATH: path to SQLite DB file

## Run locally

```
pip install -r requirements.txt
python bot.py
```

## Railway deploy
- Pre-deploy: `pip install -r requirements.txt`
- Start: `python bot.py`
- Set environment variables in the Railway dashboard as shown in .env

## Commands
- `/ping` → `pong`
- `/link` → returns your personal invite link
- `/myreferrals` → shows `Sizning odamlaringiz: N`

## How referrals work
- The bot creates invite links named `ref_<user_id>`.
- When a user joins the group via such a link, the referrer gets 1 credit (no duplicates thanks to a unique index).
- If that user’s status becomes `left` or `kicked`, the corresponding row is removed.

## Database schema
- `channel_joins(referrer_id INTEGER, user_id INTEGER, joined_at DATETIME DEFAULT CURRENT_TIMESTAMP)`
- Unique index: `(referrer_id, user_id)`
