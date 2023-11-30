import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QAction, QActionGroup
from qt_material import apply_stylesheet, list_themes

from GUI.MainWindow import Ui_MainWindow
from utilities.GptRequest import GptThreadSummarise, GptThreadChatting
from utilities.GuiHelper import FileDialog, fileNotFound, OutputLogger, isChosen
from utilities.TextFeatures import TextExtractor

OUTPUT_LOGGER_STDOUT = OutputLogger(sys.stdout, OutputLogger.Severity.DEBUG)
OUTPUT_LOGGER_STDERR = OutputLogger(sys.stderr, OutputLogger.Severity.ERROR)

sys.stdout = OUTPUT_LOGGER_STDOUT
sys.stderr = OUTPUT_LOGGER_STDERR


class start_window(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(start_window, self).__init__(parent)
        self.setupUi(self)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.stacked = QtWidgets.QStackedWidget(self)
        self.start_window = start_window(self)
        self.setCentralWidget(self.stacked)
        self.stacked.addWidget(self.start_window)

        # QtStyleTools.add_menu_theme(self, parent=self, menu=self.menu)

        self.chat_field = self.start_window.textEdit
        self.chat_field.setMinimumHeight(50)
        self.text = ""
        self.extension = ""
        self.user_field = self.start_window.textEdit_2
        self.chat_field_text = ""
        self.pushButton = self.start_window.pushButton
        self.pushButton_2 = self.start_window.pushButton_2
        self.Image = None
        self.image_path = None

        # Кнопка старт и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton.clicked.connect(self.start_script)
        # Кнопка выбора картинки и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton_2.clicked.connect(self.browse_folder)  # Выполнить функцию browse_folder

        self.gpt_thread = None

        self.menu = self.start_window.menu
        self.menu.triggered.connect(self.changeTheme)

        # Создаем группу для радиокнопок
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)

        # Добавляем радиокнопки в группу и в подменю
        themes = list_themes()
        for theme in themes:
            action = QAction(theme, self, checkable=True)
            action.setActionGroup(self.theme_group)
            self.menu.addAction(action)
            self.theme_group.addAction(action)

        self.start_window.tabWidget.currentChanged.connect(self.tabCreate)

        action = QAction("Только суммаризация", self, checkable=True)
        self.summarization = self.start_window.menu_3
        self.summarization.addAction(action)
        self.is_chosen_file = False
        self.is_summarisation = False
        self.summarization.triggered.connect(self.funcSum)

    def funcSum(self):
        if not self.is_summarisation:
            self.is_summarisation = True
        else:
            self.is_summarisation = False

    def tabCreate(self):
        cur = self.sender().tabText(self.sender().currentIndex())
        if cur == "+":
            self.sender().setTabText(self.sender().currentIndex(), f'Чат {self.start_window.tabWidget.count()}')
            chat_widget = self.create_chat_widget()
            self.sender().addTab(chat_widget, "+")
            self.sender().setCurrentIndex(self.sender().count() + 1)

    def create_chat_widget(self):
        new_chat_widget = QWidget(self)
        return new_chat_widget

    def changeTheme(self):
        selected = self.theme_group.checkedAction().text()
        apply_stylesheet(self, theme=selected)

    def start_script(self):
        if self.user_field.toPlainText():
            self.text = self.user_field.toPlainText()
            if self.is_summarisation:
                self.chat_field_text += f"Я: Суммаризируй содержимое {self.extension}-файла на русском:\n{self.text}\n"
            else:
                self.chat_field_text += f"Я: {self.text}\n"
            # self.chat_field.setText(f"Я: {self.text}\n")
            self.user_field.clear()
            print(self.user_field.toPlainText())
            # Остановить предыдущий поток, если он существует
            if self.gpt_thread and self.gpt_thread.isRunning():
                self.gpt_thread.terminate()
                self.gpt_thread.wait()

            # Создание и запуск нового потока
            self.gpt_thread = GptThreadChatting(self.text) if not self.is_summarisation else GptThreadSummarise(
                self.text, self.extension)
            self.gpt_thread.gpt_result.connect(self.update_summary_text)
            self.gpt_thread.start()
            self.user_field.clear()
            self.is_chosen_file = False
        else:
            isChosen()

    def update_summary_text(self, text, error):
        if error == 0:
            # Добавляем текст с новой строки и префиксом, например, "Бот:"
            self.chat_field_text += text
            # Обновляем текст виджета
            self.chat_field.setText(self.chat_field_text)
        else:
            self.chat_field_text += f"\nАдмин: Ошибка при запросе к API: {text}\n\n"
            print(f"\nАдмин: Ошибка при запросе к API: {text}\n\n")

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

    # window.setFixedSize()
    window.setMinimumSize(1162, 935)
    # window.setMinimumSize(window.width(), window.height())
    # window.setMaximumSize(window.width(), window.height())
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == "__main__":
    main()
