import requests
import logging
import os

# Telegram Bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# Function to send a message to Telegram
def send_telegram_message(message):
    try:
        chat_ids = get_chat_ids()
        if not chat_ids:
            logging.error("No chat IDs found where the bot is admin or in private chats.")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        for chat_id in chat_ids:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload)
            logging.info(f"Sending to Telegram chat {chat_id}: {message}")
            logging.info(f"Telegram response: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

# Function to get chat IDs from Telegram
def get_chat_ids():
    try:
        logging.info("Fetching updates to identify chat IDs...")
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(updates_url)
        if response.status_code != 200:
            logging.error(f"Failed to fetch updates: {response.status_code}, {response.text}")
            return []
        data = response.json()
        chat_ids = set()

        if 'result' in data:
            for update in data['result']:
                if 'message' in update or 'channel_post' in update:
                    chat = update.get('message', update.get('channel_post')).get('chat')
                    chat_id = chat['id']
                    chat_type = chat['type']
                    logging.info(f"Found chat ID: {chat_id} of type {chat_type}. Checking if bot is an admin...")
                    if chat_type == 'private':
                        chat_ids.add(chat_id)
                    else:
                        admin_check_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatAdministrators?chat_id={chat_id}"
                        admin_response = requests.get(admin_check_url)
                        admin_data = admin_response.json()
                        if admin_response.status_code == 200 and 'result' in admin_data:
                            for admin in admin_data['result']:
                                if admin['user']['id'] == int(TELEGRAM_BOT_TOKEN.split(':')[0]):
                                    chat_ids.add(chat_id)
        return list(chat_ids)
    except Exception as e:
        logging.error(f"Failed to get chat IDs: {e}")
        return []
