"""gpt"""
import g4f
from PyQt5.QtCore import pyqtSignal, QThread


class GptThreadSummarise(QThread):
    gpt_result = pyqtSignal(str, int)

    def __init__(self, text, extension):
        super().__init__()
        self.text = text
        self.extension = extension

    def run(self):
        try:
            if self.text:
                text = f"Суммаризируй содержимое {self.extension}-файла на русском:\n" + self.text
                text = text[:10000]
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[{"role": "user", "content": text}],
                    provider=g4f.Provider.GeekGpt,
                    stream=True
                )
                self.gpt_result.emit("\nБот: ", 2)
                for message in response:
                    self.gpt_result.emit(message, 0)
                self.gpt_result.emit("\n\n", 0)
        except Exception as e:
            self.gpt_result.emit(str(e), 1)


class GptThreadChatting(QThread):
    gpt_result = pyqtSignal(str, int)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            if self.text:
                text = self.text
                text = text[:10000]
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[{"role": "user", "content": text}],
                    provider=g4f.Provider.GeekGpt,
                    stream=True
                )
                self.gpt_result.emit("\nБот: ", 0)
                for message in response:
                    self.gpt_result.emit(message, 0)
                self.gpt_result.emit("\n\n", 0)
        except Exception as e:
            self.gpt_result.emit(str(e), 1)