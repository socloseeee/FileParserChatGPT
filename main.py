import os
import sys
import asyncio
import threading

import g4f
from PyQt5 import QtWidgets
from PyQt5.Qt import QThread
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QStyleFactory
from qt_material import apply_stylesheet, QtStyleTools

from utilities.GptRequest import GptThreadSummarise, GptThreadChatting
# from utilities.GptRequest import callGpt
from utilities.TextFeatures import TextExtractor
from utilities.GuiHelper import FileDialog, fileNotFound, LabelStretcher, OutputLogger, isChosen

from GUI.MainWindow import Ui_MainWindow


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

        self.extracted_text = self.start_window.textEdit
        self.text = ""
        self.extension = ""
        self.summary_text = self.start_window.textEdit_2
        self.summary_text_text = ""
        self.pushButton = self.start_window.pushButton
        self.pushButton_2 = self.start_window.pushButton_2
        self.Image = None
        self.image_path = None

        # Кнопка старт и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton.clicked.connect(self.start_script)
        # Кнопка выбора картинки и функция реагирующая на нажатия и перенаправляющая в метод start_script
        self.pushButton_2.clicked.connect(self.browse_folder)  # Выполнить функцию browse_folder

        self.gpt_thread = None

    def start_script(self):
        if self.image_path:
            self.extracted_text.setText(self.extracted_text.toPlainText() + "\n")
            if os.path.exists(self.image_path):
                self.extracted_text.setText(self.extracted_text.toPlainText() + "\n")
                print(self.extracted_text.toPlainText())
                # Остановить предыдущий поток, если он существует
                if self.gpt_thread and self.gpt_thread.isRunning():
                    self.gpt_thread.terminate()
                    self.gpt_thread.wait()

                # Создание и запуск нового потока
                self.gpt_thread = GptThreadSummarise(self.extracted_text.toPlainText(), self.extension)
                self.gpt_thread.gpt_result.connect(self.update_summary_text)
                self.gpt_thread.start()
                self.image_path = None
            else:
                fileNotFound()
        elif self.extracted_text.toPlainText() and not self.image_path:
            self.extracted_text.setText(self.extracted_text.toPlainText() + "\n")
            self.text = self.extracted_text.toPlainText() if self.extracted_text.toPlainText().count(
                "\n") == 1 else self.extracted_text.toPlainText()[self.extracted_text.toPlainText()[:-2].rfind("\n"):]
            print(self.text)
            # Остановить предыдущий поток, если он существует
            if self.gpt_thread and self.gpt_thread.isRunning():
                self.gpt_thread.terminate()
                self.gpt_thread.wait()

            # Создание и запуск нового потока
            self.gpt_thread = GptThreadChatting(self.text)
            self.gpt_thread.gpt_result.connect(self.update_summary_text)
            self.gpt_thread.start()
        else:
            isChosen()

    def finishedAction(self):
        self.summary_text.setText(self.summary_text.toPlainText() + "\n")

    def update_summary_text(self, text, error):
        if error == 0:
            self.summary_text_text += text
            self.summary_text.setText(self.summary_text_text)
            #LabelStretcher(self.summary_text)
        else:
            print(f"Ошибка при запросе к API: {text}")

    def browse_folder(self):
        fileName = FileDialog(
            str(os.path.abspath('assets'))
        )

        if fileName:
            self.image_path = fileName
            with TextExtractor(self.image_path) as text_extractor:
                text = text_extractor.extract_text()
                self.text = text
                self.extension = text_extractor.extension
                self.extracted_text.setText(self.extracted_text.toPlainText() + "\n" + text)
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
    apply_stylesheet(app, theme='dark_lightgreen.xml')
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.setWindowTitle('Summarize')
    window.setFixedSize(1162, 895)
    # window.setMinimumSize(window.width(), window.height())
    # window.setMaximumSize(window.width(), window.height())
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == "__main__":
    main()
