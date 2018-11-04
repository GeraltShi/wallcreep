import requests
import urllib.request
from bs4 import BeautifulSoup
import os
import time
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QSlider, QHBoxLayout, QVBoxLayout, QLabel, \
    QPlainTextEdit, QProgressBar, QGridLayout, QCheckBox
from PyQt5.QtCore import QCoreApplication, Qt, QRandomGenerator, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QImage
# import numpy as np
import sys
import logging

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        
class DataThread(QThread):
    _signal = pyqtSignal(int, bool)

    def __init__(self):
        super(DataThread, self).__init__()

    def __del__(self):
        self.wait()

    def run(self):
        head = 'https://wallpapersite.com'
        url = 'https://wallpapersite.com/?page=1'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select("div.pics > p > a")
        folder_path = './downloads/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        self._signal.emit(len(items), True)

        for index, item in enumerate(items):
            if item:
                html = head + item.get('href')
                sub_response = requests.get(html, headers=headers)
                sub_soup = BeautifulSoup(sub_response.content, 'html.parser')
                sub_items = sub_soup.select("div.pic-left > div > span.res-ttl > a.original")
                sub_img = head + sub_items[0].get('href')
                img_name = folder_path + sub_img.strip().split('/')[-1]
                with open(img_name, 'wb') as file:
                    file.write(requests.get(sub_img).content)
                    file.flush()
                file.close()
                self._signal.emit(index + 1, False)
        self._signal.emit(0, False)

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.on_init()

    def on_init(self):
        self.thread = DataThread()
        # -----------------Widgets--------------#
        # TODO: Add different sections, page selection and recursive mode
        self.button_start = QPushButton('Start', self)
        self.button_quit = QPushButton('Quit', self)
        self.logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)
        self.progress = QProgressBar()
        # -----------------Slot-----------------#
        self.button_start.clicked.connect(self.start)
        self.button_quit.clicked.connect(self.quit)
        # -----------------Layout---------------#
        self.layout_main = QVBoxLayout()
        self.layout_main.addWidget(self.button_start)
        self.layout_log = QVBoxLayout()
        self.layout_log.addWidget(self.logTextBox.widget)
        self.layout_main.addLayout(self.layout_log)
        self.layout_main.addWidget(self.progress)
        self.layout_main.addWidget(self.button_quit)
        self.setLayout(self.layout_main)
        self.setGeometry(300, 300 ,300 ,300)
        self.setWindowTitle('Wallcreep')
        self.batch_size = 0

    def callback(self, result, length_vld):
        if length_vld:
            self.batch_size = result
        else:
            if self.batch_size is not 0:
                if result is not 0:
                    logging.info('%d wallpapers downloaded' % result)
                    self.progress.setValue(result/self.batch_size*100)
                else:
                    logging.info('Download Success')
            else:
                logging.info('No wallpapers found')

    @pyqtSlot()
    def start(self):
        self.thread._signal.connect(self.callback)
        self.thread.start()

    @pyqtSlot()
    def quit(self):
        QCoreApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())