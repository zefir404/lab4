import telebot
from telebot import types
import json
import os

API_TOKEN = '8548331204:AAHQU31oVEk-pY5cNSgL-iZW4TP_2_jiC1o'
DATA_FILE = 'notes.json'

bot = telebot.TeleBot(API_TOKEN)

# --- Service Layer ---
class NotesService:
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load_data(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_data(self, data):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except IOError:
            return False

    def add_note(self, user_id, title, content):
        data = self._load_data()
        user_id = str(user_id)
        if user_id not in data:
            data[user_id] = []
        note_id = len(data[user_id]) + 1
        note = {'id': note_id, 'title': title, 'content': content}
        data[user_id].append(note)
        return self._save_data(data)

    def get_notes(self, user_id):
        data = self._load_data()
        return data.get(str(user_id), [])


service = NotesService(DATA_FILE)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)