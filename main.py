import telebot
from telebot import types
import json
import os

API_TOKEN = '8548331204:AAHQU31oVEk-pY5cNSgL-iZW4TP_2_jiC1o'
DATA_FILE = 'notes.json'

bot = telebot.TeleBot(API_TOKEN)

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
        note = {
            'id': note_id,
            'title': title,
            'content': content
        }
        data[user_id].append(note)
        return self._save_data(data)

    def get_notes(self, user_id):
        data = self._load_data()
        return data.get(str(user_id), [])

    def edit_note(self, user_id, note_id, new_title, new_content):
        data = self._load_data()
        user_id = str(user_id)
        if user_id in data:
            for note in data[user_id]:
                if note['id'] == note_id:
                    note['title'] = new_title
                    note['content'] = new_content
                    return self._save_data(data)
        return False

    def delete_note(self, user_id, note_id):
        data = self._load_data()
        user_id = str(user_id)
        if user_id in data:
            original_len = len(data[user_id])
            data[user_id] = [n for n in data[user_id] if n['id'] != note_id]

            if len(data[user_id]) < original_len:
                for index, note in enumerate(data[user_id]):
                    note['id'] = index + 1
                return self._save_data(data)
        return False

service = NotesService(DATA_FILE)


def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Создать заметку")
    btn2 = types.KeyboardButton("Мои заметки")
    btn3 = types.KeyboardButton("Редактировать")
    btn4 = types.KeyboardButton("Удалить заметку")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я бот для управления заметками.\n"
                 "Выбери действие в меню ниже:",
                 reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "Создать заметку")
def create_note_step1(message):
    msg = bot.send_message(message.chat.id, "Введите заголовок заметки:")
    bot.register_next_step_handler(msg, process_create_title)

def process_create_title(message):
    title = message.text
    msg = bot.send_message(message.chat.id, "Теперь введите текст заметки:")
    bot.register_next_step_handler(msg, process_create_content, title)

def process_create_content(message, title):
    if service.add_note(message.chat.id, title, message.text):
        bot.send_message(message.chat.id, "Заметка сохранена!", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "Ошибка сохранения.")

@bot.message_handler(func=lambda message: message.text == "Мои заметки")
def list_notes(message):
    notes = service.get_notes(message.chat.id)
    if not notes:
        bot.send_message(message.chat.id, "У вас пока нет заметок.")
    else:
        response = "Ваши заметки:\n\n"
        for note in notes:
            response += f"ID *{note['id']}* | *{note['title']}*\n{note['content']}\n{'-'*20}\n"
        bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "Редактировать")
def edit_note_step1(message):
    notes = service.get_notes(message.chat.id)
    if not notes:
        bot.send_message(message.chat.id, "Список пуст, редактировать нечего.")
        return

    text_list = "Введите *ID* заметки, которую хотите изменить:\n"
    for note in notes:
        text_list += f"{note['id']}. {note['title']}\n"

    msg = bot.send_message(message.chat.id, text_list, parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_edit_id)

def process_edit_id(message):
    try:
        note_id = int(message.text)
        notes = service.get_notes(message.chat.id)

        target_note = next((n for n in notes if n['id'] == note_id), None)

        if target_note:
            msg = bot.send_message(message.chat.id,
                f"Редактируем: *{target_note['title']}*\n"
                "Введите новый ЗАГОЛОВОК (или отправьте точку `.`, чтобы оставить старый):",
                parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_edit_title, note_id, target_note)
        else:
            bot.send_message(message.chat.id, "Заметка с таким ID не найдена.", reply_markup=main_menu_keyboard())

    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом.", reply_markup=main_menu_keyboard())

def process_edit_title(message, note_id, old_note):
    new_title = message.text
    if new_title.strip() == '.':
        new_title = old_note['title']

    msg = bot.send_message(message.chat.id,
                           "Введите новый ТЕКСТ (или отправьте точку `.`, чтобы оставить старый):")
    bot.register_next_step_handler(msg, process_edit_content, note_id, new_title, old_note)

def process_edit_content(message, note_id, new_title, old_note):
    new_content = message.text
    if new_content.strip() == '.':
        new_content = old_note['content']

    if service.edit_note(message.chat.id, note_id, new_title, new_content):
        bot.send_message(message.chat.id, "Заметка успешно обновлена!", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "Ошибка при обновлении.")

@bot.message_handler(func=lambda message: message.text == "Удалить заметку")
def delete_note_step1(message):
    msg = bot.send_message(message.chat.id, "Введите ID заметки для удаления:")
    bot.register_next_step_handler(msg, process_delete_step)

def process_delete_step(message):
    try:
        note_id = int(message.text)
        if service.delete_note(message.chat.id, note_id):
            bot.send_message(message.chat.id, "Заметка удалена.", reply_markup=main_menu_keyboard())
        else:
            bot.send_message(message.chat.id, "Не найдено.", reply_markup=main_menu_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Нужно ввести число.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)