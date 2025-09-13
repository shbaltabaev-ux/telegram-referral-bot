import asyncio
import logging
import os
import sqlite3
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) if os.getenv("CHANNEL_ID") else None
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = os.getenv("DB_PATH", "referrals.db")

if not BOT_TOKEN or not CHANNEL_ID:
    raise SystemExit("Missing BOT_TOKEN or CHANNEL_ID in environment")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ---- DB helpers ----

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS channel_joins (
            referrer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (referrer_id, user_id)
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_channel_joins_ref_user
        ON channel_joins(referrer_id, user_id)
        """
    )
    conn.commit()
    conn.close()


def referral_count(referrer_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM channel_joins WHERE referrer_id=?", (referrer_id,))
    (n,) = cur.fetchone()
    conn.close()
    return int(n)


def credit_referral(referrer_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO channel_joins(referrer_id, user_id) VALUES(?, ?)",
        (referrer_id, user_id),
    )
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def remove_referral_rows_for_user(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM channel_joins WHERE user_id=?", (user_id,))
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n


# ---- Utils ----
async def get_personal_invite_link(user_id: int) -> Optional[str]:
    try:
        link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            name=f"ref_{user_id}",
            creates_join_request=False,
        )
        return link.invite_link
    except Exception as e:
        logging.error(f"Invite link error for {user_id}: {e}")
        return None


# ---- Silence in groups ----
@dp.message(F.chat.type.in_({"group", "supergroup", "channel"}))
async def swallow_groups(_: Message):
    return


# ---- Commands (DM only) ----
@dp.message(Command("ping"), F.chat.type == "private")
async def cmd_ping(m: Message):
    await m.reply("pong")


@dp.message(Command("link"), F.chat.type == "private")
async def cmd_link(m: Message):
    link = await get_personal_invite_link(m.from_user.id)
    if link:
        await m.reply(f"🔗 Sizning guruh havolangiz:\n{link}")
    else:
        await m.reply("Havola yaratib bo'lmadi. Keyinroq urinib ko'ring.")


@dp.message(Command("myreferrals"), F.chat.type == "private")
async def cmd_myreferrals(m: Message):
    n = referral_count(m.from_user.id)
    await m.reply(f"<b>Sizning odamlaringiz</b>: <b>{n}</b>", parse_mode="HTML")


# ---- Member updates in the target group ----
@dp.chat_member(F.chat.id == CHANNEL_ID)
async def on_member_update(ev: ChatMemberUpdated):
    old = ev.old_chat_member.status
    new = ev.new_chat_member.status
    uid = ev.new_chat_member.user.id

    # Joined (first transition to member/administrator/creator)
    if old in {"left", "kicked"} and new in {"member", "administrator", "creator"}:
        inv = getattr(ev, "invite_link", None)
        name = getattr(inv, "name", "") if inv else ""
        if name.startswith("ref_"):
            try:
                referrer_id = int(name.split("_", 1)[1])
            except Exception:
                return
            if credit_referral(referrer_id, uid):
                try:
                    first = ev.new_chat_member.user.first_name or "Foydalanuvchi"
                    await bot.send_message(referrer_id, f"🎉 {first} guruhga qo'shildi!")
                except Exception as e:
                    logging.warning(f"Notify error: {e}")

    # Left/kicked -> remove any rows for that user
    if old in {"member", "administrator", "creator"} and new in {"left", "kicked"}:
        remove_referral_rows_for_user(uid)


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db()

    # Ensure webhook is removed to avoid conflicts
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
