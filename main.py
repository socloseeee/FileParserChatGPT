import os
import sys
import sqlite3

import g4f
import langchain.chat_models.gigachat

langchain.chat_models.GigaChat()
from summa import summarizer

from PyQt5 import QtWidgets, QtGui
from qt_material import apply_stylesheet, list_themes
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup

from utilities.TextFeatures import TextExtractor
from utilities.GuiHelper import FileDialog, isChosen, appendText, appendHtml
from GUI.TabMainWindow import Ui_MainWindow, Ui_InsideTabWindow
from utilities.GptRequest import GptThread

# globals
is_summarisation = False
tabIndex = 0
model = g4f.Provider.GeekGpt


class main_window(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(main_window, self).__init__(parent)
        self.setupUi(self)


class tabbed_window(QtWidgets.QMainWindow, Ui_InsideTabWindow):
    def __init__(self, parent=None):
        super(tabbed_window, self).__init__(parent)
        self.setupUi(self)


class InsideTabWindow(QtWidgets.QMainWindow):
    def __init__(self, tab_name):
        super().__init__()

        self.tab_name = tab_name

        # vars
        self.text = ""
        self.sumChat = None
        self.extension = ""
        self.image_path = None
        self.gpt_thread = None
        self.chat_field_text = ""
        self.user_field_text = ""
        self.is_chosen_file = False

        # windows
        self.stacked = QtWidgets.QStackedWidget(self)
        self.tabbed_window = tabbed_window(self)
        self.setCentralWidget(self.stacked)
        self.stacked.addWidget(self.tabbed_window)
        self.main_window = main_window()

        # text_fields
        self.chat_field = self.tabbed_window.textEdit
        self.tabbed_window.textEdit.ensureCursorVisible()
        self.chat_field.setReadOnly(True)
        # self.chat_field.setWordWrapMode(QTextOption.NoWrap)
        # self.chat_field.document().setMaximumBlockCount(100)
        self.user_field = self.tabbed_window.textEdit_2

        # buttons
        self.pushButton = self.tabbed_window.pushButton
        self.pushButton_2 = self.tabbed_window.pushButton_2

        # Кнопка старт и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton.clicked.connect(self.start_script)

        # Кнопка выбора картинки и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton_2.clicked.connect(self.browse_folder)  # Выполнить функцию browse_folder

    def start_script(self):
        if self.user_field.toPlainText():
            global is_summarisation, model
            self.text = self.user_field.toPlainText()
            html = """
            <img src="static/user3.jpg" alt="Image" height="40" width="40">
            """
            # print(self.text, self.chat_field_text)
            if is_summarisation:
                appendHtml(self.chat_field, html)
                text = f"\nЯ: Суммаризируй содержимое {self.extension}-файла на русском:\n{self.text}\n"
                self.chat_field_text += text
                appendText(self.chat_field, text)
            else:
                # self.chat_field.insertHtml(html)
                appendHtml(self.chat_field, html)
                text = f"\nЯ: {self.text}\n"
                self.chat_field_text += text
                appendText(self.chat_field, text)
            self.chat_field.verticalScrollBar().setValue(self.chat_field.verticalScrollBar().maximum())
            # print(self.user_field.toPlainText())

            # Остановить предыдущий поток, если он существует
            if self.gpt_thread and self.gpt_thread.isRunning():
                self.gpt_thread.terminate()
                self.gpt_thread.wait()

            # Создание и запуск нового потока
            self.gpt_thread = GptThread(self.text, self.extension, model, self.tab_name, is_summarisation)
            self.gpt_thread.gpt_result.connect(self.update_summary_text)
            self.gpt_thread.updateDB.connect(self.UpdateChat)
            self.gpt_thread.start()
            self.user_field_text = self.user_field.toPlainText()
            self.user_field.clear()
            self.is_chosen_file = False
        else:
            isChosen()

    def update_summary_text(self, text, error):
        if error == 0:
            if text == "\nБот: ":
                html = """
                <img src="static/gpt5.jpg" alt="Image" height="40" width="40">
                """
                appendHtml(self.chat_field, html)
            # Добавляем текст с новой строки и префиксом, например, "Бот:"
            self.chat_field_text += text
            appendText(self.chat_field, text)
        else:
            if text != "\nБот: ":
                # print(text.strip())
                self.chat_field_text += f"\nОшибка при запросе к API: {text}\n\n"
                appendText(self.chat_field, f"\nОшибка при запросе к API: {text}\n\n")
                # print(f"\nОшибка при запросе к API: {text}\n\n")
        self.chat_field.verticalScrollBar().setValue(self.chat_field.verticalScrollBar().maximum())

    def UpdateChat(self):
        global tabIndex
        # print(self.chat_field_text)
        serialized_data = {
            'Chat': self.chat_field.toPlainText(),
            'summarisedVal': summarizer.summarize(self.chat_field.toPlainText(), ratio=0.05)
        }

        connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
        cursor = connection.cursor()

        # Insert serialized data into the table
        cursor.execute('''
            UPDATE tabWidgets 
            SET Chat = ?,
                summarisedVal = ? 
            WHERE "Index" = ?
        ''', (
            serialized_data['Chat'],
            serialized_data['summarisedVal'],
            tabIndex + 1,
        )
                       )

        connection.commit()
        connection.close()

    def browse_folder(self):
        fileName = FileDialog(
            str(os.path.abspath('assets'))
        )

        if fileName:
            self.image_path = fileName
            with TextExtractor(self.image_path) as text_extractor:
                self.is_chosen_file = True
                text = text_extractor.extract_text()
                self.text = text
                self.extension = text_extractor.extension
                self.user_field.setText(self.text)
                with open("output.txt", "w", encoding="UTF-8") as file:
                    file.write(text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # vars
        self.clear = False
        self.Return = False
        self.removing_tabs = False
        self.all_chats_container = []

        # windows
        self.stacked = QtWidgets.QStackedWidget(self)
        self.main_window = main_window(self)
        self.setCentralWidget(self.stacked)
        self.stacked.addWidget(self.main_window)

        # menu
        self.menu = self.main_window.menu
        self.menu.triggered.connect(self.changeTheme)

        # Добавляем радиокнопки в группу и в подменю
        themes = list_themes()

        # Создаем группу для радиокнопок
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        for theme in themes:
            action = QAction(theme, self, checkable=True)
            action.setActionGroup(self.theme_group)
            self.menu.addAction(action)
            self.theme_group.addAction(action)

        action = QAction("Только суммаризация", self, checkable=True)
        self.summarization = self.main_window.menu_3
        self.summarization.addAction(action)
        self.summarization.triggered.connect(self.funcSum)

        self.theme_group_2 = QActionGroup(self)
        self.theme_group_2.setExclusive(True)

        action = QAction("Очистить все чаты", self, checkable=True)
        self.clearOrReturnChats = self.main_window.menu_4
        self.clearOrReturnChats.addAction(action)
        self.theme_group_2.addAction(action)

        action = QAction("Вернуть чаты", self, checkable=True)
        self.clearOrReturnChats.addAction(action)
        self.theme_group_2.addAction(action)

        self.clearOrReturnChats.triggered.connect(self.funcClearOrReturn)

        _providers = [
            # g4f.Provider.Aichat, inactiave
            g4f.Provider.ChatBase,
            # g4f.Provider.Bing,  # proxy
            # g4f.Provider.GptGo,  # proxy
            # g4f.Provider.You,  # proxy
            # g4f.Provider.Yqcloud,
            g4f.Provider.GeekGpt,  # too many requests
            # g4f.Provider.Acytoo,
            # g4f.Provider.AiAsk,
            # g4f.Provider.AItianhu,
            # g4f.Provider.Bard,
            # g4f.Provider.ChatAnywhere,
            # g4f.Provider.ChatForAi,
            # g4f.Provider.Phind,
            langchain.chat_models.gigachat.GigaChat
        ]

        self.theme_group_3 = QActionGroup(self)
        self.theme_group_3.setExclusive(True)

        for provider in _providers:
            action = QAction(provider.__name__, self, checkable=True)
            action.setActionGroup(self.theme_group_3)
            self.main_window.menu_5.addAction(action)
            self.theme_group_3.addAction(action)

        self.main_window.menu_5.triggered.connect(self.changeProvider)

        # tabs
        # print(self.load_from_database("tabWidgets"))
        for index, chat, summarized_val, chat_name in self.load_from_database("tabWidgets"):
            self.removing_tabs = False
            chat_widget = self.create_chat_widget(chat, chat_name, summarized_val)
            self.main_window.tabWidget.addTab(chat_widget, chat_name)
        self.main_window.tabWidget.currentChanged.connect(self.tabCreate)

    def changeProvider(self, action):
        global model
        if action.text() != "GigaChat":
            model = eval("g4f.Provider." + action.text())
        else:
            model = langchain.chat_models.gigachat
            # print(model.__name__)

    def funcClearOrReturn(self, action):
        selected = action.text()
        source_connection = sqlite3.connect('database/db.sqlite3')
        source_cursor = source_connection.cursor()

        if selected == "Очистить все чаты" and not self.clear:
            self.clear = True
            self.Return = False
            # Выбор и сохранение данных из tabWidgets в backupWidgets
            source_cursor.execute('SELECT * FROM tabWidgets')
            rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))

            source_cursor.execute('DELETE FROM backupWidgets')
            source_connection.commit()

            source_cursor.executemany(
                'INSERT INTO backupWidgets(Chat, summarisedVal, ChatName) VALUES (?, ?, ?)', rows_to_transfer
            )
            source_connection.commit()

            # Очистка данных в tabWidgets
            source_cursor.execute('DELETE FROM tabWidgets')
            source_connection.commit()

            # Добавление пустых чатов в tabWidgets
            source_cursor.execute(
                'INSERT INTO tabWidgets (Chat, summarisedVal, ChatName) VALUES (?, ?, ?), (?, ?, ?)',
                ("", "", "Чат 1", "", "", "+")
            )
            source_connection.commit()

            # Обновление виджета tabWidget
            # self.main_window.tabWidget.clear()
            self.remove_all_tabs()
            self.all_chats_container.clear()

            # Загрузка данных из tabWidgets и добавление их в tabWidget
            for index, chat, summarized_val, chat_name in source_cursor.execute("SELECT * FROM tabWidgets"):
                self.removing_tabs = False
                chat_widget = self.create_chat_widget(chat, chat_name, summarized_val)
                self.main_window.tabWidget.addTab(chat_widget, chat_name)

            source_connection.close()
            # action.setChecked(False)

        elif selected == "Вернуть чаты" and not self.Return:
            self.Return = True
            self.clear = False
            # Очистка данных в tabWidgets
            source_cursor.execute('DELETE FROM tabWidgets')
            source_connection.commit()

            # Выбор и сохранение данных из backupWidgets в tabWidgets
            source_cursor.execute('SELECT * FROM backupWidgets')
            rows_to_transfer = list(map(lambda x: x[1:], source_cursor.fetchall()))

            source_cursor.executemany(
                'INSERT INTO tabWidgets(Chat, summarisedVal, ChatName) VALUES (?, ?, ?)', rows_to_transfer
            )
            source_connection.commit()

            # Обновление виджета tabWidget
            # self.main_window.tabWidget.clear()
            self.remove_all_tabs()
            self.all_chats_container.clear()

            # Загрузка данных из tabWidgets и добавление их в tabWidget
            for index, chat, summarized_val, chat_name in source_cursor.execute("SELECT * FROM tabWidgets"):
                self.removing_tabs = False
                chat_widget = self.create_chat_widget(chat, chat_name, summarized_val)
                self.main_window.tabWidget.addTab(chat_widget, chat_name)

            source_connection.close()
            #
            # action.setChecked(False)

    def remove_all_tabs(self):
        # Добавляем флаг, указывающий, что идет процесс удаления вкладок
        self.removing_tabs = True
        while self.main_window.tabWidget.count() > 0:
            widget = self.main_window.tabWidget.widget(0)
            self.main_window.tabWidget.removeTab(0)
            widget.setParent(None)
        # Удаляем флаг после завершения удаления вкладок
        del self.removing_tabs

    def save_to_database(self):
        # print(self.main_window.tabWidget.currentWidget().objectName())
        serialized_data = {
            'Chat': "",  # obj.chat_field_text
            'summarisedVal': "",  # summarizer.summarize(obj.chat_field_text, ratio=0.1)
            'ChatName': "+"
        }

        connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
        cursor = connection.cursor()

        # Insert serialized data into the table
        cursor.execute('''
            INSERT INTO tabWidgets (Chat, summarisedVal, ChatName)
            VALUES (?, ?, ?)
        ''', (
            serialized_data['Chat'],
            serialized_data['summarisedVal'],
            serialized_data['ChatName'],
        )
                       )

        connection.commit()
        connection.close()

    def load_from_database(self, table):
        connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
        cursor = connection.cursor()

        # Select all rows from the table
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()

        connection.close()

        return rows

    def funcSum(self):
        global is_summarisation
        if not is_summarisation:
            is_summarisation = True
        else:
            is_summarisation = False

    def exchangeOld_to_database(self):
        # print(self.main_window.tabWidget.currentWidget().objectName())
        serialized_data = {
            'Chat': "",  # obj.chat_field_text
            'summarisedVal': "",  # summarizer.summarize(obj.chat_field_text, ratio=0.1)
            'ChatName': f"Чат {self.main_window.tabWidget.count() - 1}"
        }

        connection = sqlite3.connect('database/db.sqlite3')  # Replace with your database name
        cursor = connection.cursor()

        # Insert serialized data into the table
        cursor.execute('''
            UPDATE tabWidgets SET ChatName = ? WHERE ChatName = "+"
        ''', (serialized_data['ChatName'],)
                       )

        connection.commit()
        connection.close()

    def tabCreate(self):
        global tabIndex
        if hasattr(self, 'removing_tabs') and self.removing_tabs:
            return
        tabIndex = self.main_window.tabWidget.currentIndex()
        cur = self.sender().tabText(self.sender().currentIndex())
        if cur == "+":
            self.sender().setTabText(self.sender().currentIndex(), f'Чат {self.main_window.tabWidget.count()}')
            self.all_chats_container[-1].tab_name = f'Чат {self.main_window.tabWidget.count()}'
            chat_widget = self.create_chat_widget("", "+", "")
            self.sender().addTab(chat_widget, "+")
            self.sender().setCurrentIndex(self.sender().count() + 1)
            self.exchangeOld_to_database()
            self.save_to_database()
            # self.all_chats_container.append(chat_widget)
            # print(self.all_chats_container)

    def create_chat_widget(self, chat, chat_name, sum_val):
        new_chat = InsideTabWindow(chat_name)
        new_chat.chat_field_text = chat
        new_chat.chat_field.setText(chat)
        new_chat.sumChat = sum_val
        self.all_chats_container.append(new_chat)
        return new_chat

    def changeTheme(self):
        selected = self.theme_group.checkedAction().text()
        apply_stylesheet(self, theme=selected)


def main():
    try:
        # Включить в блок try/except, для Mac/Linux
        from PyQt5.QtWinExtras import QtWin  # !!!

        myappid = 'mycompany.myproduct.subproduct.version'  # !!!
        QtWin.setCurrentProcessExplicitAppUserModelID(myappid)  # !!!
    except ImportError:
        pass

    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    apply_stylesheet(app, theme='dark_medical.xml')
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.setWindowTitle('GptChat')
    window.setMinimumSize(1162, 935)
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == "__main__":
    main()
