import sqlite3
from datetime import datetime


def clearAllChats(source_connection, source_cursor):
    # Выбор и сохранение данных из Messages в backupMessages
    source_cursor.execute('SELECT * FROM Messages')
    rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))
    # (rows_to_transfer)
    source_cursor.execute('DELETE FROM Messages')
    source_connection.commit()

    source_cursor.executemany(
        'INSERT INTO backupMessages(content, role, model, provider, chat_id, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)', rows_to_transfer
    )
    source_connection.commit()

    source_cursor.execute('SELECT * FROM Chat')
    rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))
    source_cursor.execute('DELETE FROM Chat')
    source_connection.commit()

    source_cursor.executemany(
        'INSERT INTO backupChat(chat_name, created_at, modified_at)'
        'VALUES (?, ?, ?)', rows_to_transfer
    )

    # Добавление пустых чатов в Chat
    source_cursor.execute(
        'INSERT INTO Chat'
        '(chat_name, created_at, modified_at) '
        'VALUES (?, ?, ?), (?, ?, ?)',
        (
            "Чат 1",
            datetime.now().strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "+",
            "",
            ""
        )
    )
    source_connection.commit()


def returnAllChats(source_connection, source_cursor):
    source_cursor.execute('DELETE FROM Chat')
    source_connection.commit()

    # Очистка данных в Chat
    source_cursor.execute('SELECT * FROM backupChat')
    rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))
    # (rows_to_transfer)
    # source_cursor.execute('DELETE FROM backupChat')
    # source_connection.commit()

    source_cursor.executemany(
        'INSERT INTO Chat(chat_name, created_at, modified_at) '
        'VALUES (?, ?, ?)', rows_to_transfer
    )
    source_connection.commit()

    source_cursor.execute('DELETE FROM Messages')
    source_connection.commit()

    source_cursor.execute('SELECT * FROM backupMessages')
    rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))
    # (rows_to_transfer)

    source_cursor.execute('DELETE FROM backupMessages')
    source_cursor.execute('DELETE FROM backupChat')
    source_connection.commit()

    source_cursor.executemany(
        'INSERT INTO Messages(content, role, model, provider, chat_id, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)', rows_to_transfer
    )
    source_connection.commit()


def appendMessage(content, role, tabIndex, provider, model_dict):
    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()

    message_data = {
        "content": content,
        "role": role,
        "model": model_dict[provider.__name__],
        "provider": provider.__name__,
        "chat_id": tabIndex + 1,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    # Вставка данных в таблицу (без указания message_id)
    cursor.execute("""
        INSERT INTO Messages 
        (content, role, model, provider, chat_id, created_at) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        message_data["content"],
        message_data["role"],
        message_data["model"],
        message_data["provider"],
        message_data["chat_id"],
        message_data["created_at"]
    ))

    connection.commit()
    connection.close()


def load_from_database(table, query=''):
    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()

    # Select all rows from the table
    if not query:
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
    else:
        cursor.execute(f'{query}')
        rows = cursor.fetchall()

    connection.close()

    return rows


def save_to_database(tabIndex):
    # (self.main_window.tabWidget.currentWidget().objectName())
    serialized_data = {
        'chat_id': tabIndex + 2,  # obj.chat_field_text
        'chat_name': "+",  # summarizer.summarize(obj.chat_field_text, ratio=0.1)
        'created_at': "",
        'modified_at': ""
    }

    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()

    # Insert serialized data into the table
    cursor.execute('''
        INSERT INTO Chat (chat_id, chat_name, created_at, modified_at)
        VALUES (?, ?, ?, ?)
    ''', (
        serialized_data['chat_id'],
        serialized_data['chat_name'],
        serialized_data['created_at'],
        serialized_data['modified_at']
    )
                   )

    connection.commit()
    connection.close()


def exchangeOld_to_database(tabsCount):
    # (self.main_window.tabWidget.currentWidget().objectName())
    serialized_data = {
        'chat_name': f"Чат {tabsCount - 1}",
        'created_at': datetime.now().strftime('%Y-%m-%d'),
        'modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()

    # Insert serialized data into the table
    cursor.execute('''
        UPDATE Chat 
        SET chat_name = ?,
            created_at = ?,
            modified_at = ?
        WHERE chat_name = "+"
    ''', (
        serialized_data['chat_name'],
        serialized_data['created_at'],
        serialized_data['modified_at'],
    )
                   )

    connection.commit()
    connection.close()


def saveSettings2DB(provider, tabIndex, theme, is_summarisation, language):
    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()

    cursor.execute('''
            UPDATE Settings 
            SET provider = ?,
                tabIndex = ?,
                theme = ?,
                summarization = ?,
                language = ?
            ''', (
        f"{provider}"[f"{provider}".index("'") + 1:f"{provider}".rindex(".")],
        tabIndex,
        theme,
        is_summarisation,
        language
    )
                   )

    connection.commit()
    connection.close()


def loadSettings():
    connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
    cursor = connection.cursor()
    return cursor.execute("SELECT * FROM Settings").fetchone()
