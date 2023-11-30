import os

from PyQt5 import QtCore
from PyQt5.QtCore import QEvent, QObject, pyqtSignal
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox


class OutputLogger(QObject):
    emit_write = pyqtSignal(str, int)

    class Severity:
        DEBUG = 0
        ERROR = 1

    def __init__(self, io_stream, severity):
        super().__init__()

        self.io_stream = io_stream
        self.severity = severity

    def write(self, text):
        self.io_stream.write(text)
        self.emit_write.emit(text, self.severity)

    def flush(self):
        self.io_stream.flush()


def FileDialog(directory='', forOpen=True, fmt='', isFolder=False) -> str:
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    options |= QFileDialog.DontUseCustomDirectoryIcons
    dialog = QFileDialog()
    dialog.setOptions(options)

    dialog.setFilter(dialog.filter() | QtCore.QDir.Hidden)

    # ARE WE TALKING ABOUT FILES OR FOLDERS
    if isFolder:
        dialog.setFileMode(QFileDialog.DirectoryOnly)
    else:
        dialog.setFileMode(QFileDialog.AnyFile)
    # OPENING OR SAVING
    dialog.setAcceptMode(QFileDialog.AcceptOpen) if forOpen else dialog.setAcceptMode(QFileDialog.AcceptSave)

    # SET FORMAT, IF SPECIFIED
    if fmt != '' and isFolder is False:
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f'{fmt} (*.{fmt})'])

    # SET THE STARTING DIRECTORY
    if directory != '':
        dialog.setDirectory(str(directory))
    else:
        dialog.setDirectory(str(os.getcwd()))

    if dialog.exec_() == QDialog.Accepted:
        path = dialog.selectedFiles()[0]  # returns a list
        return path
    else:
        return ''


class LabelStretcher(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.apply(parent)

    def apply(self, label):
        if label:
            label.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if ev.type() != QEvent.Resize:
            return False
        label = obj
        # if not label or not label.text() or not label.hasScaledContents():
        #     print('s')
        #     return False
        print("pre:", label.minimumSizeHint(), label.sizeHint(), label.size())

        def dSize(inner, outer):
            dy = inner.height() - outer.height()
            dx = inner.width() - outer.width()
            return max(dx, dy)

        def f(fontSize, label):
            font = label.font()
            font.setPointSizeF(fontSize)
            label.setFont(font)
            d = dSize(label.sizeHint(), label.size())
            print("f:", fontSize, "d", d)
            return d

        def df(fontSize, label):
            if fontSize < 1.0:
                fontSize = 1.0
            return f(fontSize + 0.5, label) - f(fontSize - 0.5, label)

        # Newton's method
        font = label.font()
        fontSize = font.pointSizeF()
        for i in range(5):
            d = df(fontSize, label)
            print("d:", d)
            if d < 0.1:
                break
            fontSize -= f(fontSize, label) / d
        font.setPointSizeF(fontSize)
        label.setFont(font)
        print("post:", i, label.minimumSizeHint(), label.sizeHint(), label.size())

        return False


def isChosen():
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText("Ошибка")
    msgBox.setInformativeText("Введите текст или выберите файл!")
    msgBox.setWindowTitle("Ошибка")
    msgBox.exec_()


def fileNotFound():
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText("Ошибка")
    msgBox.setInformativeText("Файл не найден!")
    msgBox.setWindowTitle("Ошибка")
    msgBox.exec_()
