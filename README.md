# Telegram Announcement Bot

A simple Telegram bot (aiogram 3.x + SQLite) that lets you broadcast text or
photo announcements to multiple groups at once, from a private control panel.

## Features

- `/start` command with a private control panel (admin-only)
- Automatically saves every group where the bot is added/promoted as admin
- Automatically removes a group if the bot is removed or demoted
- View all connected groups
- Select All / Unselect All / select groups individually
- Send a **text** announcement or a **photo with caption**
- Same message is copied to every selected group
- Shows success/failed count after sending
- Automatically handles Telegram FloodWait (rate limit) errors
- No duplicate groups (enforced by a UNIQUE constraint in SQLite)

## Project Structure

```
announcement-bot/
├── main.py           # Bot entry point and all handlers
├── database.py        # SQLite helper functions
├── keyboards.py        # Inline keyboards
├── config.py           # BOT_TOKEN and ADMIN_IDS
├── requirements.txt
└── README.md
```

## Setup

1. **Create a bot** with [@BotFather](https://t.me/BotFather) and copy the token.

2. **Get your Telegram user ID** from [@userinfobot](https://t.me/userinfobot).

3. **Edit `config.py`**:

   ```python
   BOT_TOKEN = "123456789:AAAA...your-real-token..."
   ADMIN_IDS = [111111111]  # your Telegram user ID
   ```

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the bot**:

   ```bash
   python main.py
   ```

## How to use

1. Add the bot to a group and **promote it to admin**. It will be saved to
   the database automatically (no command needed).
2. Open a private chat with the bot and send `/start`.
3. Tap **View Groups** to see all connected groups.
4. Tap groups to select/unselect them, or use **Select All** / **Unselect All**.
5. Tap **Send Announcement**, choose **Text** or **Photo + Caption**, then
   send the content when prompted.
6. Confirm to broadcast. You'll get a report with success/failed counts.

## Notes

- Only users listed in `ADMIN_IDS` can use the control panel.
- The bot must remain an **admin** in a group to keep sending messages there.
- `bot.db` (SQLite file) is created automatically on first run in the same
  folder as `main.py`.
- If a group removes the bot's admin rights or removes the bot, it is
  automatically dropped from the database.
