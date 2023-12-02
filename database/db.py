import pickle
import sqlite3
from summa import summarizer


# Сериализация объекта InsideTabWindow
def serialize_inside_tab_window(obj, index):
    # Здесь вам нужно определить, какие данные вы хотите сохранить
    serialized_data = {
        'Index': index,
        'Chat': obj.textEdit.toPlainText(),
        'summarisedVal': summarizer.summarize(obj.textEdit.toPlainText(), ratio=0.1),
    }
    return pickle.dumps(serialized_data)


# Пример сохранения объекта InsideTabWindow в базу данных
def save_inside_tab_window_to_db(tab_window_obj):
    serialized_data = serialize_inside_tab_window(tab_window_obj)

    # Подключение к базе данных (SQLite в данном примере)
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Замените 'your_table' и 'your_column' на реальные названия вашей таблицы и колонки
    cursor.execute('INSERT INTO your_table (your_column) VALUES (?)', (serialized_data,))

    conn.commit()
    conn.close()


# Пример загрузки данных из базы данных и десериализации
def load_inside_tab_window_from_db(obj):
    # Подключение к базе данных (SQLite в данном примере)
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Замените 'your_table' и 'your_column' на реальные названия вашей таблицы и колонки
    cursor.execute('SELECT your_column FROM your_table')
    serialized_data = cursor.fetchone()[0]

    # Десериализация данных
    deserialized_data = pickle.loads(serialized_data)

    # Создание нового объекта InsideTabWindow и восстановление данных
    new_tab_window_obj = obj
    new_tab_window_obj.some_attribute = deserialized_data['some_attribute']
    # Восстановите другие атрибуты

    conn.close()

    return new_tab_window_obj
