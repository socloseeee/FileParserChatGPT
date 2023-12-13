"""gpt"""
import g4f
import configparser
from PyQt5.QtCore import pyqtSignal, QThread
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.gigachat import GigaChat
from langchain_core.callbacks import BaseCallbackHandler


config = configparser.ConfigParser()
config.read('credentials.ini')
value1 = config.get('Section1', 'variable1')

class StreamHandler(BaseCallbackHandler):
    def __init__(self, signal):
        self.signal = signal

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"{token}", end="", flush=True)
        self.signal.emit(token, 0)


class GptThread(QThread):
    gpt_result = pyqtSignal(str, int)
    updateDB = pyqtSignal()

    def __init__(self, text, extension, model, isSummarisation):
        super().__init__()
        self.model = model
        self.text = text
        self.extension = extension
        self.isSummarisation = isSummarisation

    def run(self):
        try:
            if self.text:
                text = self.text if not self.isSummarisation else \
                    f"Суммаризируй содержимое {self.extension}-файла на русском:\n" + self.text
                text = text[:10000]
                if self.model == "GigaChat":
                    self.GigachatRun(text)
                else:
                    self.OtherModelRun(text)
                self.gpt_result.emit("\n\n", 0)
                self.updateDB.emit()
        except Exception as e:
            self.gpt_result.emit(str(e), 1)

    def GigachatRun(self, text):
        messages = [
            HumanMessage(content=text)
        ]
        self.gpt_result.emit(f"\nБот: ", 0)
        chat = GigaChat(
            credentials=value1,
            scope="GIGACHAT_API_CORP",
            verify_ssl_certs=False,
            streaming=True,
            callbacks=[StreamHandler(self.gpt_result)]
        )
        response = chat(messages).content

    def OtherModelRun(self, text):
        import time

        max_retries = 10  # Максимальное количество попыток

        for attempt in range(max_retries):
            try:
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[{"role": "user", "content": text}],
                    provider=g4f.Provider.GeekGpt,
                    stream=True
                )
                # Продолжаем обработку response
                self.gpt_result.emit("\nБот: ", 0)
                for message in response:
                    self.gpt_result.emit(message, 0)
                self.gpt_result.emit("\n\n", 0)
                self.updateDB.emit()
                break  # Выход из цикла, если запрос выполнен успешно
            except Exception as e:
                print(f"Ошибка: {e}")
                if attempt < max_retries - 1:
                    print(f"Повторная попытка через 5 секунд...")
                    self.gpt_result.emit(f"{attempt + 1}-я попытка: {e}\nПовторная попытка через 5 секунд...", 1)
                    time.sleep(5)  # Подождать 30 секунд перед повторной попыткой
                else:
                    self.gpt_result.emit("\nПревышено максимальное количество попыток. Прекращаем.", 1)
                    print("Превышено максимальное количество попыток. Прекращаем.")
                    break

