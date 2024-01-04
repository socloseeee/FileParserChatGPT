import os
import sys
import sqlite3

import g4f
import langchain.chat_models.gigachat

from PyQt5 import QtWidgets, QtGui
from langchain.chat_models.gigachat import GigaChat
from qt_material import apply_stylesheet, list_themes
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup

from utilities.DbHelper import appendMessage, clearAllChats, returnAllChats, load_from_database, \
    exchangeOld_to_database, save_to_database, loadSettings, saveSettings2DB
from utilities.TextFeatures import TextExtractor
from utilities.GuiHelper import FileDialog, isChosen, appendText, appendHtml
from GUI.TabMainWindow import Ui_MainWindow, Ui_InsideTabWindow
from utilities.GptRequest import GptThread

# globals
provider, tabIndex, theme, is_summarisation, language = loadSettings()
provider = eval(provider)

model_dict = {
    "GeekGpt": "Gpt-3.5",
    "ChatBase": "Gpt-3.5",
    "GigaChat": "ruGPT-3"
}


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
            global is_summarisation, tabIndex, provider, model_dict
            self.text = self.user_field.toPlainText()
            html = """
            <img src="static/user3.jpg" alt="Image" height="40" width="40">
            """
            # (self.text, self.chat_field_text)
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
            # (self.user_field.toPlainText())
            # Остановить предыдущий поток, если он существует
            if self.gpt_thread and self.gpt_thread.isRunning():
                self.gpt_thread.terminate()
                self.gpt_thread.wait()

            # Создание и запуск нового потока
            self.gpt_thread = GptThread(self.text, self.extension, provider, self.tab_name, is_summarisation, tabIndex,
                                        provider, model_dict)
            self.gpt_thread.gpt_result.connect(self.update_summary_text)
            self.gpt_thread.updateDB.connect(appendMessage)
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
            if '```' in text:
                text = text[:text.index("```")] + """<pre><code class="python">"""
            self.chat_field_text += text
            appendText(self.chat_field, text)
        else:
            if text != "\nБот: ":
                # (text.strip())
                self.chat_field_text += f"\nОшибка при запросе к API: {text}\n\n"
                appendText(self.chat_field, f"\nОшибка при запросе к API: {text}\n\n")
                # (f"\nОшибка при запросе к API: {text}\n\n")
        self.chat_field.verticalScrollBar().setValue(self.chat_field.verticalScrollBar().maximum())

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


def changeProvider(action):
    global provider
    if action.text() != "GigaChat":
        provider = eval("g4f.Provider." + action.text())
    else:
        provider = GigaChat


def funcSum():
    global is_summarisation
    if not is_summarisation:
        is_summarisation = True
    else:
        is_summarisation = False


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
        for them in themes:
            action = QAction(them, self, checkable=True)
            if them == theme:
                action.setChecked(True)
            action.setActionGroup(self.theme_group)
            self.menu.addAction(action)
            self.theme_group.addAction(action)

        action = QAction("Только суммаризация", self, checkable=True)
        if is_summarisation:
            action.setChecked(True)
        self.summarization = self.main_window.menu_3
        self.summarization.addAction(action)
        self.summarization.triggered.connect(funcSum)

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

        for prov in _providers:
            action = QAction(prov.__name__, self, checkable=True)
            if prov == provider:
                action.setChecked(True)
            action.setActionGroup(self.theme_group_3)
            self.main_window.menu_5.addAction(action)
            self.theme_group_3.addAction(action)

        self.main_window.menu_5.triggered.connect(changeProvider)

        self.createTabs(
            self.main_window,
            self.tabCreate,
            self.create_chat_widget
        )
        self.main_window.tabWidget.currentChanged.connect(self.tabCreate)

    def funcClearOrReturn(self, action):
        selected = action.text()
        source_connection = sqlite3.connect('database/db.sqlite3')
        source_cursor = source_connection.cursor()

        if selected == "Очистить все чаты" and not self.clear:
            self.clear = True
            self.Return = False

            # dbManipulations
            clearAllChats(source_connection, source_cursor)

            # Обновление виджета tabWidget
            self.remove_all_tabs()
            self.all_chats_container.clear()

            # Загрузка данных из Chat и добавление их в tabWidget
            self.createTabs(
                self.main_window,
                self.tabCreate,
                self.create_chat_widget
            )

            source_connection.close()
            # action.setChecked(False)

        elif selected == "Вернуть чаты" and not self.Return and self.clear:
            self.Return = True
            self.clear = False

            returnAllChats(source_connection, source_cursor)

            self.remove_all_tabs()
            self.all_chats_container.clear()

            # Загрузка данных из Chat и добавление их в tabWidget
            self.createTabs(
                self.main_window,
                self.tabCreate,
                self.create_chat_widget
            )
            source_connection.close()
            #
            # action.setChecked(False)

    def createTabs(self, main_window, tabCreate, create_chat_widget, query=''):
        for index, chat_name, created_at, modified_at in load_from_database("Chat"):
            self.removing_tabs = False
            messages = load_from_database(
                "Messages",
                query=f"SELECT *\n"
                      f"FROM Messages\n"
                      f"WHERE chat_id={index}"
            )
            chat_widget = create_chat_widget(chat_name, messages)
            main_window.tabWidget.addTab(chat_widget, chat_name)
        main_window.tabWidget.currentChanged.connect(tabCreate)

    def remove_all_tabs(self):
        # Добавляем флаг, указывающий, что идет процесс удаления вкладок
        self.removing_tabs = True
        while self.main_window.tabWidget.count() > 0:
            widget = self.main_window.tabWidget.widget(0)
            self.main_window.tabWidget.removeTab(0)
            widget.setParent(None)
        # Удаляем флаг после завершения удаления вкладок
        del self.removing_tabs

    def tabCreate(self):
        global tabIndex
        if hasattr(self, 'removing_tabs') and self.removing_tabs:
            return
        tabIndex = self.main_window.tabWidget.currentIndex()
        cur = self.sender().tabText(self.sender().currentIndex())
        if cur == "+":
            self.sender().setTabText(self.sender().currentIndex(), f'Чат {self.main_window.tabWidget.count()}')
            self.all_chats_container[-1].tab_name = f'Чат {self.main_window.tabWidget.count()}'
            chat_widget = self.create_chat_widget("+", "")
            self.sender().addTab(chat_widget, "+")
            self.sender().setCurrentIndex(self.sender().count() + 1)
            exchangeOld_to_database(self.main_window.tabWidget.count())
            save_to_database(tabIndex)
            # self.all_chats_container.append(chat_widget)
            # (self.all_chats_container)

    def create_chat_widget(self, chat_name, messages):
        new_chat = InsideTabWindow(chat_name)
        # (messages)
        for user_message, bot_message in zip(messages[::2], messages[1::2]):
            appendHtml(new_chat.chat_field, """
                <img src="static/user3.jpg" alt="Image" height="40" width="40">
                """)
            appendText(new_chat.chat_field, "\nЯ: " + user_message[1] + "\n")
            appendHtml(new_chat.chat_field, """
                <img src="static/gpt5.jpg" alt="Image" height="40" width="40">
                """)
            appendText(new_chat.chat_field, "\nБот: " + bot_message[1] + "\n\n")
            new_chat.chat_field_text += user_message[1] + bot_message[1]
        # new_chat.chat_field_text = chat
        # new_chat.chat_field.setText(chat)
        self.all_chats_container.append(new_chat)
        return new_chat

    def changeTheme(self):
        global theme
        theme = self.theme_group.checkedAction().text()
        apply_stylesheet(self, theme=theme)

    def closeEvent(self, event):
        # Ваш код для сохранения данных в базу данных перед закрытием приложения
        saveSettings2DB(provider, tabIndex, theme, is_summarisation, language)
        event.accept()


def main():
    try:
        # Включить в блок try/except, для Mac/Linux
        from PyQt5.QtWinExtras import QtWin  # !!!

        myappid = 'mycompany.myproduct.subproduct.version'  # !!!
        QtWin.setCurrentProcessExplicitAppUserModelID(myappid)  # !!!
    except ImportError:
        pass

    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    app.setWindowIcon(QtGui.QIcon('static/app_logo_cropped.jpg'))
    apply_stylesheet(app, theme=theme)
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.setWindowTitle('GptChat')
    window.resize(1162, 935)
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == "__main__":
    main()
