import requests
import logging
import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def send_telegram_message(message):
    try:
        chat_ids = get_chat_ids()
        if not chat_ids:
            logging.error("No chat IDs found.")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        for chat_id in chat_ids:
            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(url, data=payload)
            logging.info(f"Sent message to chat {chat_id}. Response: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def get_chat_ids():
    try:
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(updates_url)
        data = response.json()
        chat_ids = {update['message']['chat']['id'] for update in data.get('result', []) if 'message' in update}
        return list(chat_ids)
    except Exception as e:
        logging.error(f"Failed to get chat IDs: {e}")
        return []
