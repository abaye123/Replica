import os
import json
import sys
import subprocess
import threading
from datetime import datetime
from io import StringIO
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QRadioButton, QButtonGroup, QCheckBox, 
    QPushButton, QFileDialog, QMessageBox, QTextEdit, QProgressBar,
    QGroupBox, QStatusBar, QDialog, QTabWidget, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QCursor

if os.name == 'nt':  # Windows
    APP_DATA_DIR = os.path.join(os.environ.get('APPDATA', ''), 'Replica')
elif os.name == 'posix':  # Linux, Mac
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.config', 'Replica')
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Replica')

if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)

CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


class DownloadThread(QThread):
    update_progress = Signal(str)
    update_console = Signal(str)
    download_finished = Signal(int, int)
    download_error = Signal(str)

    def __init__(self, urls, format_option, save_directory, show_cli):
        super().__init__()
        self.urls = urls
        self.format_option = format_option
        self.save_directory = save_directory
        self.show_cli = show_cli
        self.running = True

    def run(self):
        total_urls = len(self.urls)
        successful = 0
        failed = 0

        for i, url in enumerate(self.urls, 1):
            if not self.running:
                break

            self.update_progress.emit(f"מוריד {i}/{total_urls}: {url}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_template = os.path.join(self.save_directory, f"%(title)s_{timestamp}.%(ext)s")
            
            command = self.format_option + ["-o", output_template, url]
            
            if self.show_cli:
                self.update_console.emit(f"\n{'='*50}\nמתחיל הורדה של: {url}\nפקודה: {' '.join(command)}\n{'='*50}\n\n")
            
            try:
                process = subprocess.Popen(
                    command, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                if self.show_cli:
                    for line in process.stdout:
                        self.update_console.emit(line)
                
                exit_code = process.wait()
                
                if exit_code == 0:
                    successful += 1
                    if self.show_cli:
                        self.update_console.emit(f"\n✓ ההורדה של {url} הושלמה בהצלחה!\n\n")
                else:
                    failed += 1
                    error_output = process.stderr.read()
                    if self.show_cli:
                        self.update_console.emit(f"\n❌ שגיאה בהורדה של {url}. קוד יציאה: {exit_code}\n")
                        self.update_console.emit(f"פרטי שגיאה: {error_output}\n\n")
            
            except FileNotFoundError:
                failed += 1
                error_msg = "yt-dlp לא נמצא במערכת. ודא שהתקנת אותו ושהוא נגיש מ-PATH."
                self.download_error.emit(error_msg)
                if self.show_cli:
                    self.update_console.emit(f"\n❌ שגיאה: {error_msg}\n\n")
                break

        if self.running:
            summary = f"הושלם: {successful}/{total_urls} הורדות הצליחו, {failed}/{total_urls} נכשלו"
            if self.show_cli:
                self.update_console.emit(f"\n{'='*50}\n{summary}\n{'='*50}\n")
            
            self.update_progress.emit(summary)
            self.download_finished.emit(successful, failed)

    def stop(self):
        self.running = False


class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.setWindowTitle("הגדרות")
        self.setMinimumSize(500, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title_label = QLabel("הגדרות Replica")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        save_group = QGroupBox("תיקיית ברירת מחדל לשמירה")
        save_layout = QHBoxLayout()
        save_group.setLayout(save_layout)
        
        self.save_dir_edit = QLineEdit()
        self.save_dir_edit.setText(self.config.get("save_dir", os.path.join(os.path.expanduser("~"), "Downloads", "Replica")))
        save_layout.addWidget(self.save_dir_edit)
        
        browse_btn = QPushButton("בחר")
        browse_btn.clicked.connect(self.select_directory)
        save_layout.addWidget(browse_btn)
        
        layout.addWidget(save_group)
        
        security_group = QGroupBox("אפשרויות אבטחה")
        security_layout = QVBoxLayout()
        security_group.setLayout(security_layout)
        
        self.ssl_check = QCheckBox("כבה בדיקת SSL (השתמש עם --no-check-certificate)")
        self.ssl_check.setChecked(self.config.get("ssl_check", True))
        security_layout.addWidget(self.ssl_check)
        
        layout.addWidget(security_group)
        
        display_group = QGroupBox("אפשרויות תצוגה")
        display_layout = QVBoxLayout()
        display_group.setLayout(display_layout)
        
        self.show_cli_check = QCheckBox("הצג את פלט ה-CLI של yt-dlp")
        self.show_cli_check.setChecked(self.config.get("show_cli", True))
        display_layout.addWidget(self.show_cli_check)
        
        self.dark_mode_check = QCheckBox("מצב כהה")
        self.dark_mode_check.setChecked(self.config.get("dark_mode", False))
        display_layout.addWidget(self.dark_mode_check)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("ביטול")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("שמור")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
    
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "בחר תיקייה לשמירת קבצים")
        if directory:
            self.save_dir_edit.setText(directory)
    
    def get_settings(self):
        return {
            "save_dir": self.save_dir_edit.text(),
            "ssl_check": self.ssl_check.isChecked(),
            "show_cli": self.show_cli_check.isChecked(),
            "dark_mode": self.dark_mode_check.isChecked()
        }


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("אודות")
        self.setFixedSize(350, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title_label = QLabel("Replica")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        desc_label = QLabel("תוכנה להורדת סרטונים ואודיו מ-YouTube וממקורות אחרים")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addSpacing(20)
        
        dev_group = QGroupBox()
        dev_layout = QVBoxLayout()
        dev_group.setLayout(dev_layout)
        
        about_label = QLabel(
            "רפליקה (Replica) היא מעטפת GUI של yt-dlp<br>"
            '<a href="https://github.com/yt-dlp/yt-dlp">https://github.com/yt-dlp/yt-dlp</a><br><br>'
            'המבוססת על הפרוייקט הזה'
            '<br><a href="https://github.com/AshiVered/CobaltYT_dlp">https://github.com/AshiVered/CobaltYT_dlp</a><br><br>'
           'רפליקה שוכתבה ועוצבה מחדש ע"י abaye<br>'
            '<a href="https://github.com/abaye123/Replica">https://github.com/abaye123/Replica</a><br><br>'
            '© 2025'
        )
        about_label.setOpenExternalLinks(True)
        about_label.setWordWrap(True)
        about_label.setAlignment(Qt.AlignCenter)
        dev_layout.addWidget(about_label)
        
        layout.addWidget(dev_group)
        
        layout.addStretch()
        
        close_btn = QPushButton("סגור")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = load_config()
        
        self.setWindowTitle("Replica")
        self.setMinimumSize(650, 600)
        
        if self.config.get("dark_mode", False):
            self.set_dark_mode()
        
        self.setup_ui()
        
        self.download_thread = None
    
    def set_dark_mode(self):
        dark_style = """
        QMainWindow, QDialog {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        QWidget {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
        }
        QPushButton {
            background-color: #0d6efd;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #0b5ed7;
        }
        QPushButton:pressed {
            background-color: #0a58ca;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 2px;
        }
        QRadioButton, QCheckBox {
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QStatusBar {
            background-color: #252525;
            color: #ffffff;
        }
        """
        self.setStyleSheet(dark_style)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        main_layout.addLayout(header_layout)
        
        title_label = QLabel("Replica")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        btn_layout = QHBoxLayout()
        header_layout.addLayout(btn_layout)
        
        btn_layout.addStretch()
        
        about_btn = QPushButton("אודות")
        about_btn.clicked.connect(self.show_about)
        btn_layout.addWidget(about_btn)
        
        settings_btn = QPushButton("הגדרות")
        settings_btn.clicked.connect(self.show_settings)
        btn_layout.addWidget(settings_btn)
        
        main_layout.addSpacing(10)
        
        url_group = QGroupBox()
        url_layout = QVBoxLayout()
        url_group.setLayout(url_layout)
        
        url_label = QLabel("הכנס קישורים לסרטונים, ערוצים או פלייליסטים (מופרדים בפסיק):")
        url_layout.addWidget(url_label)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(self.url_edit)
        
        #self.url_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.url_edit.customContextMenuRequested.connect(self.show_context_menu)
        
        main_layout.addWidget(url_group)
        
        format_quality_layout = QHBoxLayout()
        main_layout.addLayout(format_quality_layout)
        
        format_group = QGroupBox("בחר פורמט")
        format_layout = QVBoxLayout()
        format_group.setLayout(format_layout)
        
        self.format_mp4 = QRadioButton("MP4 (וידאו)")
        self.format_mp4.setChecked(True)
        format_layout.addWidget(self.format_mp4)
        
        self.format_mp3 = QRadioButton("MP3 (אודיו)")
        format_layout.addWidget(self.format_mp3)
        
        self.format_group = QButtonGroup()
        self.format_group.addButton(self.format_mp4, 1)
        self.format_group.addButton(self.format_mp3, 2)
        self.format_group.buttonClicked.connect(self.toggle_quality_options)
        
        format_quality_layout.addWidget(format_group)
        
        self.quality_group = QGroupBox("בחר איכות")
        quality_layout = QVBoxLayout()
        self.quality_group.setLayout(quality_layout)
        
        self.quality_high = QRadioButton("איכות גבוהה")
        self.quality_high.setChecked(True)
        quality_layout.addWidget(self.quality_high)
        
        self.quality_low = QRadioButton("איכות נמוכה")
        quality_layout.addWidget(self.quality_low)
        
        self.quality_button_group = QButtonGroup()
        self.quality_button_group.addButton(self.quality_high, 1)
        self.quality_button_group.addButton(self.quality_low, 2)
        
        format_quality_layout.addWidget(self.quality_group)
        
        download_layout = QHBoxLayout()
        main_layout.addLayout(download_layout)
        
        download_layout.addStretch()
        self.download_btn = QPushButton("התחל הורדה")
        self.download_btn.setMinimumSize(120, 40)
        download_font = QFont()
        download_font.setBold(True)
        self.download_btn.setFont(download_font)
        self.download_btn.clicked.connect(self.start_download)
        download_layout.addWidget(self.download_btn)
        download_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        self.cli_group = QGroupBox("פלט תהליך ההורדה")
        cli_layout = QVBoxLayout()
        self.cli_group.setLayout(cli_layout)
        
        cli_header_layout = QHBoxLayout()
        cli_layout.addLayout(cli_header_layout)
        
        clear_btn = QPushButton("נקה")
        clear_btn.clicked.connect(self.clear_console)
        cli_header_layout.addWidget(clear_btn)
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", 10))
        cli_layout.addWidget(self.console_text)
        
        if self.config.get("show_cli", True):
            main_layout.addWidget(self.cli_group)
        else:
            self.cli_group.hide()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Replica מוכן להורדה")
        
        self.toggle_quality_options()
    
    def show_context_menu(self, position):
        context_menu = QMenu()
        paste_action = context_menu.addAction("הדבק")
        paste_action.triggered.connect(lambda: self.url_edit.paste())
        copy_action = context_menu.addAction("העתק")
        copy_action.triggered.connect(lambda: self.url_edit.copy())
        cut_action = context_menu.addAction("גזור")
        cut_action.triggered.connect(lambda: self.url_edit.cut())
        
        context_menu.exec_(self.url_edit.mapToGlobal(position))
    
    def toggle_quality_options(self):
        if self.format_group.checkedId() == 1:
            self.quality_group.setEnabled(True)
        else:
            self.quality_group.setEnabled(False)
    
    def start_download(self):

        urls_input = self.url_edit.text().strip()
        if not urls_input:
            QMessageBox.warning(self, "שגיאה", "לא הוזנו קישורים.")
            return
        
        urls = [url.strip() for url in urls_input.split(",")]
        format_choice = self.format_group.checkedId()
        quality_choice = self.quality_button_group.checkedId()
        ssl_option = [] if not self.config.get("ssl_check", False) else ["--no-check-certificate"]
        
        if format_choice == 1:  # MP4
            if quality_choice == 1:  # איכות גבוהה
                format_option = ["yt-dlp"] + ssl_option
            elif quality_choice == 2:  # איכות נמוכה
                format_option = ["yt-dlp"] + ssl_option + ["-f", "mp4"]
            else:
                QMessageBox.critical(self, "שגיאה", "בחר איכות תקינה.")
                return
        elif format_choice == 2:  # MP3
            format_option = ["yt-dlp"] + ssl_option + ["-x", "--audio-format", "mp3"]
        else:
            QMessageBox.critical(self, "שגיאה", "בחר פורמט תקין.")
            return
        
        save_directory = self.config.get("save_dir", os.path.join(os.path.expanduser("~"), "Downloads", "Replica"))
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        
        self.download_btn.setEnabled(False)
        self.status_bar.showMessage(f"מוריד {len(urls)} קבצים...")
        self.progress_bar.show()
        
        if self.config.get("show_cli", True):
            self.clear_console()
        
        self.download_thread = DownloadThread(
            urls, format_option, save_directory, self.config.get("show_cli", True)
        )
        
        self.download_thread.update_progress.connect(self.update_status)
        self.download_thread.update_console.connect(self.update_console)
        self.download_thread.download_finished.connect(self.download_complete)
        self.download_thread.download_error.connect(self.show_error)
        
        self.download_thread.start()
    
    @Slot(str)
    def update_status(self, message):
        self.status_bar.showMessage(message)
    
    @Slot(str)
    def update_console(self, text):
        self.console_text.append(text)
        self.console_text.verticalScrollBar().setValue(
            self.console_text.verticalScrollBar().maximum()
        )
    
    @Slot(int, int)
    def download_complete(self, successful, failed):
        total = successful + failed
        
        self.download_btn.setEnabled(True)
        self.progress_bar.hide()
        
        if successful > 0:
            msg = f"הורדה הושלמה: {successful}/{total} קבצים הורדו בהצלחה"
            if failed > 0:
                msg += f", {failed}/{total} קבצים נכשלו."
            QMessageBox.information(self, "הצלחה", msg)
        elif failed > 0:
            QMessageBox.critical(self, "שגיאה", f"כל ההורדות נכשלו ({failed}/{total}).")
    
    @Slot(str)
    def show_error(self, message):
        QMessageBox.critical(self, "שגיאה", message)
    
    def clear_console(self):
        self.console_text.clear()
    
    def show_settings(self):
        dialog = SettingsDialog(self, self.config)
        if dialog.exec():
            old_show_cli = self.config.get("show_cli", True)
            
            self.config = dialog.get_settings()
            save_config(self.config)
            
            if dialog.get_settings().get("dark_mode") != self.config.get("dark_mode", False):
                if dialog.get_settings().get("dark_mode"):
                    self.set_dark_mode()
                else:
                    self.setStyleSheet("")
            
            new_show_cli = self.config.get("show_cli", True)
            if old_show_cli != new_show_cli:
                if new_show_cli:
                    self.cli_group.show()
                    layout = self.centralWidget().layout()
                    layout.addWidget(self.cli_group)
                else:
                    self.cli_group.hide()
                    layout = self.centralWidget().layout()
                    layout.removeWidget(self.cli_group)
    
    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(
                self, "יציאה", 
                "יש הורדה פעילה. האם אתה בטוח שברצונך לצאת?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.download_thread.stop()
                self.download_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())