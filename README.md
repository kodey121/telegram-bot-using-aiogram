# 🤖 Aiogram 3.x Support & File Management Bot

A feature-rich Telegram bot built with **Python 3.10+** and **Aiogram 3.x**. Features dynamic nested folder navigation, direct user-to-admin support routing, role-based admin controls, multi-language localization (Fluent `i18n`), photo-to-PDF generation, and social media video downloading.

---

## ✨ Features

### 🌐 Internationalization (i18n)
* Full bilingual support (**Arabic** & **English**) powered by `aiogram-i18n` and **Mozilla Fluent (`.ftl`)**.
* Dynamic variables and placeholders handled cleanly inside translation files.

### 📁 Dynamic File & Menu System
* **Nested Hierarchy**: Create multi-level folders and subfolders on the fly via inline keyboards.
* **File Library**: Upload documents and photos to specific folders.
* **File Operations**: Bulk file lists, direct file delivery, renaming folders, and deleting files/folders.

### 💬 Live Support Ticket System
* **User Support Form**: Guides users through submitting their name, grade, university ID, and issue.
* **Admin Group Dispatch**: Ticket is dispatched directly to the configured Telegram support group.
* **One-Click Reply**: Admins can reply directly to the ticket from the group using inline callbacks, sending the response straight to the user's private chat.

### 👥 Role Management & Administration
* **Multi-Tier Access Control**: Distinct privilege levels for **Users**, **Admins**, and the **Bot Owner**.
* **Admin Management**: Owner can add or remove admins dynamically by Telegram User ID.
* **Group Setup**: Configure the target support group chat ID directly from the admin panel.
* **Safe Broadcast System**: Send announcement messages to all users with live delivery reports (Success, Blocked, Failed) and Telegram rate-limit handling.

### 🛠️ Media Tools
* 🖼️ **Photo to PDF Converter**: Send single or batch photos/albums to compile and generate a unified PDF document.
* 🎬 **Social Media Video Downloader**: Fetch and download videos directly by pasting links from YouTube, Instagram, TikTok, and more.

---

## 🛠️ Project Structure

```text
├── Downloads/                # Directory for temporary downloaded media
│   ├── Pdfs/   #where the final pdf is saved but it will be deleted after sending it to the user , inside this pdfs will be {chat_id_user_id} folders whcih the info in
│   └── Photos/ #where the photos is saved before convrting them into one pdf , will be deleted after the pdf is sent to the user, inside Photos will be {chat_id_user_id} 
├── locales/                  # Localization files
│   ├── ar/                   # Arabic translation files (.ftl)
│   └── en/                   # English translation files (.ftl)
├── .env                      # Environment variables
├── .python-version           # Python version specification
├── commands.py               # Bot command handlers (/start, /help, /myid, etc.)
├── config.py                 # Configuration and settings manager
├── database.py               # SQLite database interaction module
├── keyboard.py               # Dynamic inline keyboard and menu builders
├── language_manager.py       # Language switching and i18n logic
├── LICENSE                   # Project license
├── main.py                   # Bot entry point and initialization
├── Middlware.py              # Custom Aiogram middleware
├── my_dpython --veata.db     # SQLite database file
├── photosToPdf.py            # Image-to-PDF compilation handler
├── Pipfile                   # Pipenv dependency specification
├── requirements.txt          # Python dependencies
├── settings.json             # JSON settings file
├── support.py                # Support ticketing & admin group routing logic
├── VideoDownloader.py        # Social media video extraction core
└── VideoDownloaderAiogram.py # Video downloader router & handlers
```

---

## 🚀 Quick Start

### Prerequisites
* Python **3.10** or higher.
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather).

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/kodey121/telegram_bot_aiogram.git](https://github.com/kodey121/telegram_bot_aiogram.git)
   cd telegram_bot_aiogram
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   OWNER_ID=987654321
   ```

5. **Run the bot:**
   ```bash
   python main.py
   ```

---

## ⚙️ Initial Setup & Usage

1. **Get User ID**: Any user or prospective admin can run `/myid` in private chat to get their numerical Telegram User ID.
2. **Add Admins**: As the Owner (`OWNER_ID`), open the main menu to access owner controls and add administrators.
3. **Configure Support Group**:
   - Add the bot to your designated admin support group.
   - Run `/myid` or `/group_id` inside the group chat to obtain the group ID (usually starts with `-100...`).
   - Use the Owner settings panel in the bot's private chat to set the Support Group ID.

---

## 🌐 Localization (`.ftl`)

All text strings are separated from Python logic into `.ftl` files. To modify or add new messages:

1. Edit `locales/ar/LC_MESSAGES/messages.ftl` for Arabic strings.
2. Edit `locales/en/LC_MESSAGES/messages.ftl` for English strings.
3. **Always restart the bot** after editing `.ftl` files to reload strings into memory.

Example Fluent key with parameters:
```ftl
supp-ticket-format =
    👤 User: { $name }
    💬 Message: { $message }
```

---

## 📌 Important Notes

* **Large Video Downloads**: Downloading files over **20 MB** (or **2 GB** for self-hosted Bot API instances) requires appropriate local Telegram API server setups.
* **Rate Limits**: The broadcast engine includes built-in sleep delays to comply with Telegram API flood limits automatically.
