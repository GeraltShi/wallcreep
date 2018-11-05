import requests
import urllib.request
from bs4 import BeautifulSoup
import os
import time
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QSlider, QHBoxLayout, QVBoxLayout, QLabel, \
    QPlainTextEdit, QProgressBar, QGridLayout, QCheckBox
from PyQt5.QtCore import QCoreApplication, Qt, QRandomGenerator, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QImage, QIcon
# import numpy as np
import sys
import logging

class QTextEditLogger(logging.Handler):
    """Logger of the panel"""
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        
class DownloadThread(QThread):
    """Download thread"""
    _signal = pyqtSignal(int, bool)

    def __init__(self):
        super(DownloadThread, self).__init__()
        self.page = 1

    def __del__(self):
        self.wait()

    def setpage(self, page):
        self.page = page

    def run(self):
        head = 'https://wallpapersite.com'
        url = 'https://wallpapersite.com/?page=%d' % (self.page)
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


class RefreshThread(QThread):
    """Refresh thread"""
    _signal = pyqtSignal(str)

    def __init__(self):
        super(RefreshThread, self).__init__()
        self.page = 1

    def __del__(self):
        self.wait()

    def setpage(self, page):
        self.page = page

    def run(self):
        head = 'https://wallpapersite.com'
        url = 'https://wallpapersite.com/?page=%d' %(self.page)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select("div.pics > p > a > img")
        folder_path = './thumbnails/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # self._signal.emit(len(items))
        for index, item in enumerate(items):
            if item:
                sub_img = head + item.get('src')
                img_name = folder_path + sub_img.strip().split('/')[-1]
                with open(img_name, 'wb') as file:
                    file.write(requests.get(sub_img).content)
                    file.flush()
                file.close()
                self._signal.emit(img_name)

class MainWindow(QWidget):
    """Main Window"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.on_init()

    def on_init(self):
        self.thread_download = DownloadThread()
        self.thread_download._signal.connect(self.callback_download)
        self.thread_refresh = RefreshThread()
        self.thread_refresh._signal.connect(self.callback_refresh)
        # -----------------Widgets--------------#
        # TODO: Add different sections and recursive mode, Refine UI
        self.button_next = QPushButton('>', self)
        self.button_prev = QPushButton('<', self)
        self.button_prev.setEnabled(False)
        self.button_next.clicked.connect(lambda: self.refresh(self.page + 1))
        self.button_prev.clicked.connect(lambda: self.refresh(self.page - 1))
        self.label_page = QLabel('0')
        self.label_page.setAlignment(Qt.AlignHCenter)
        self.label_page.setAlignment(Qt.AlignVCenter)
        self.picsnap = []
        for i in range(12):
            self.picsnap.append(QLabel())
        self.button_download = QPushButton('Download', self)
        self.button_download.setEnabled(False)
        self.button_quit = QPushButton('Quit', self)
        self.logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)
        self.progress = QProgressBar()
        # -----------------Slot-----------------#
        self.button_download.clicked.connect(self.download)
        self.button_quit.clicked.connect(self.quit)
        # -----------------Layout---------------#
        self.layout_main = QVBoxLayout()
        self.layout_snap = QGridLayout()
        for i in range(12):
            self.layout_snap.addWidget(self.picsnap[i], i/3, i%3)
        self.layout_top = QHBoxLayout()
        self.layout_top.addWidget(self.button_prev)
        self.layout_top.addWidget(self.label_page)
        self.layout_top.addWidget(self.button_next)
        self.layout_top.addStretch()
        self.layout_top.addWidget(self.button_download)
        self.layout_log = QVBoxLayout()
        self.layout_log.addWidget(self.logTextBox.widget)
        self.layout_bottom = QHBoxLayout()
        self.layout_bottom.addWidget(self.progress)
        self.layout_bottom.addWidget(self.button_quit)
        self.layout_main.addStretch()
        self.layout_main.addLayout(self.layout_snap)
        self.layout_main.addLayout(self.layout_top)
        self.layout_main.addLayout(self.layout_log)
        self.layout_main.addLayout(self.layout_bottom)
        self.setLayout(self.layout_main)
        self.setWindowTitle('Wallcreep')
        self.setWindowIcon(QIcon('./ico/ico.png'))
        self.setFixedSize(600, 800)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint)
        self.batch_size = 0
        self.i = 0
        self.page = 0

    def callback_download(self, result, length_vld):
        """Save pictures"""
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
        self.thread_download.quit()

    def callback_refresh(self, dir_thumb):
        """Refresh pictures on panel"""
        logging.info('%s' % dir_thumb)
        png = QPixmap(dir_thumb).scaledToWidth(200)
        self.picsnap[self.i].setPixmap(png)
        self.i = self.i + 1
        self.thread_refresh.quit()


    @pyqtSlot()
    def download(self):
        """Start the download thread"""
        self.thread_download.start()

    @pyqtSlot()
    def refresh(self, page):
        """Start the refresh thread and update ui"""
        self.thread_refresh.setpage(page)
        self.thread_refresh.start()
        self.i = 0
        self.page = page
        self.thread_download.setpage(page)
        self.label_page.setText('Page %d' % page)
        if page > 0: 
            self.button_download.setEnabled(True)
        if page > 1: 
            self.button_prev.setEnabled(True)

    @pyqtSlot()
    def quit(self):
        """Quit the app"""
        QCoreApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
