import sys
import os
import json
import socket
import base64
import io
import html
import winsound
import threading
import hashlib
from datetime import datetime
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QListWidget, QTextEdit, QLineEdit, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar,
                             QSystemTrayIcon, QMenu, QDialog, QFormLayout, QCheckBox,
                             QListWidgetItem, QTextBrowser, QGraphicsDropShadowEffect)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QSize, QSettings, 
                            QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRect,
                            QParallelAnimationGroup)
from PyQt6.QtGui import QIcon, QPixmap, QImage, QAction
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

# --- CONFIGURATION ---
ALLOWED_MGMT_USERS = ["Admin", "Manager"] # Only these names can access management features

# --- CHAT HISTORY ---
CHAT_HISTORY_FILE = "chat_history.jsonl"
MAX_HISTORY_LOAD = 100  # max messages to load on startup

# --- STYLING (QSS) ---
STYLESHEET = """
    QWidget {
        font-family: 'Segoe UI', 'Roboto', 'Montserrat', sans-serif;
        color: #2d3436;
    }
    #centralFrame {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
            stop:0 rgba(255, 255, 255, 0.9), 
            stop:1 rgba(240, 245, 255, 0.85));
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.6);
    }
    QListWidget { 
        background-color: transparent; 
        border: none; 
        outline: none;
    }
    QListWidget::item { 
        background-color: rgba(255, 255, 255, 0.5); 
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 14px;
        margin: 6px 10px;
        padding: 14px; 
        color: #2d3436;
    }
    QListWidget::item:hover {
        background-color: rgba(25, 118, 210, 0.08);
        border: 1px solid rgba(25, 118, 210, 0.2);
    }
    QListWidget::item:selected { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #42a5f5);
        color: white; 
        border: none;
        font-weight: 600;
    }
    QTextBrowser { 
        background-color: transparent; 
        border: none;
        padding: 5px;
    }
    /* Modern Slim Scrollbar */
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(0, 0, 0, 0.15);
        min-height: 30px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(25, 118, 210, 0.4);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QLineEdit { 
        background-color: white; 
        border: 1px solid rgba(0, 0, 0, 0.1); 
        border-radius: 20px; 
        padding: 10px 18px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1.5px solid #1976d2;
    }
    
    QPushButton { 
        background-color: #1976d2; 
        color: white; 
        border-radius: 18px; 
        padding: 10px 20px; 
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover { 
        background-color: #1565c0; 
    }
    QPushButton:pressed {
        background-color: #0d47a1;
        padding-top: 11px;
        padding-left: 21px;
    }
    
    #file_btn { 
        background-color: rgba(0, 0, 0, 0.04); 
        border: none; 
        border-radius: 18px;
        padding: 8px; 
    }
    #file_btn:hover { 
        background-color: rgba(25, 118, 210, 0.1); 
    }
    
    #close_btn { background-color: rgba(255, 95, 86, 0.15); color: #d32f2f; border-radius: 12px; }
    #close_btn:hover { background-color: #ff5f56; color: white; }
    
    #min_btn { background-color: rgba(255, 189, 46, 0.15); color: #f57c00; border-radius: 12px; }
    #min_btn:hover { background-color: #ffbd2e; color: white; }
    
    #settings_btn { background-color: rgba(0,0,0,0.05); border-radius: 12px; color: #555; }
    #settings_btn:hover { background-color: rgba(0,0,0,0.1); }
    
    #username_label { 
        font-size: 12px; 
        font-weight: 700; 
        color: white; 
        padding: 6px 15px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #3498db); 
        border-radius: 15px;
    }
    #mgmt_badge { 
        font-size: 9px; font-weight: 800; color: white;
        background-color: #ff3d00; border-radius: 8px; padding: 2px 6px; 
    }
    #transfer_bar_widget {
        background: white;
        border: 1px solid rgba(25, 118, 210, 0.15);
        border-radius: 16px;
        padding: 10px;
    }
    #transfer_status_label {
        font-size: 11px;
        color: #1976d2;
        font-weight: bold;
    }
    #transfer_pct_label {
        font-size: 11px;
        color: #555;
        font-weight: bold;
    }
    QProgressBar {
        border: none;
        border-radius: 5px;
        background-color: rgba(200, 220, 240, 0.6);
        height: 8px;
        text-align: center;
    }
    QProgressBar::chunk {
        border-radius: 5px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1976d2, stop:1 #42a5f5);
    }
    QProgressBar[complete="true"]::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2e7d32, stop:1 #66bb6a);
    }
"""

DARK_STYLESHEET = """
    QWidget {
        font-family: 'Segoe UI', 'Roboto', 'Montserrat', sans-serif;
        color: #e0e0e0;
    }
    #centralFrame {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
            stop:0 #1a1c2c, 
            stop:1 #11111b);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    QListWidget::item { 
        background-color: rgba(255, 255, 255, 0.05); 
        border: 1px solid rgba(255, 255, 255, 0.03);
        color: #e0e0e0;
    }
    QListWidget::item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    QListWidget::item:selected { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e66f5, stop:1 #74c7ec);
        color: white; 
    }
    QTextBrowser { background-color: transparent; }
    QLineEdit { 
        background-color: #313244; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        color: white;
    }
    #file_btn { background-color: rgba(255, 255, 255, 0.05); }
    #settings_btn { background-color: rgba(255,255,255,0.05); color: #ccc; }
    #transfer_bar_widget {
        background: #1e1e2e;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    #transfer_status_label { color: #74c7ec; }
    QProgressBar { background-color: rgba(255, 255, 255, 0.05); }
"""
"""

# --- NETWORKING THREADS ---
class DiscoveryWorker(QThread):
    user_found = pyqtSignal(str, str)
    user_lost = pyqtSignal(str)
    
    def __init__(self, port, username):
        super().__init__()
        self.port = port
        self.username = username
        self.zc = None
        self.info = None

    def run(self):
        self.zc = Zeroconf()
        self.register_me()
        self.browser = ServiceBrowser(self.zc, "_officechat._tcp.local.", self)
        self.exec()

    def register_me(self):
        local_ip = socket.gethostbyname(socket.gethostname())
        self.info = ServiceInfo("_officechat._tcp.local.", f"{self.username}._officechat._tcp.local.",
                           addresses=[socket.inet_aton(local_ip)], port=self.port)
        self.zc.register_service(self.info)

    def update_username(self, new_name):
        self.username = new_name
        if self.zc and self.info:
            self.zc.unregister_service(self.info)
            self.register_me()

    def add_service(self, zc, type, name):
        info = zc.get_service_info(type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            self.user_found.emit(name.split('.')[0], f"{ip}:{info.port}")
            
    def update_service(self, zc, type, name):
        """Method required by ServiceBrowser but no action is needed on update."""
        pass
            
    def remove_service(self, zc, type, name):
        self.user_lost.emit(name.split('.')[0])

class CommsThread(QThread):
    incoming_chat = pyqtSignal(str, str)
    file_requested = pyqtSignal(str, str, int, str)
    file_accepted = pyqtSignal(str, int)
    file_rejected = pyqtSignal(str)
    port_bound = pyqtSignal(int)
    
    def _bind_socket(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5005
        while port <= 5050:
            try:
                server.bind(('0.0.0.0', port))
                return server, port
            except OSError:
                port += 1
        return None, None

    def _receive_message(self, client):
        buffer = ""
        while True:
            try:
                chunk = client.recv(4096).decode()
                if not chunk:
                    break
                buffer += chunk
                if '\n' in buffer:
                    break
            except Exception:
                break
        return buffer.strip()

    def _handle_payload(self, buffer, addr):
        try:
            data = json.loads(buffer)
            msg_type = data.get('type')
            if msg_type == 'chat':
                self.incoming_chat.emit(addr[0], data['content'])
            elif msg_type == 'file_req':
                self.file_requested.emit(addr[0], data['filename'], data['size'], data.get('preview', ''))
            elif msg_type == 'file_accept':
                self.file_accepted.emit(addr[0], data['port'])
            elif msg_type == 'file_reject':
                self.file_rejected.emit(addr[0])
        except (json.JSONDecodeError, KeyError):
            pass # Invalid payload

    def run(self):
        server, port = self._bind_socket()
        if not server:
            return # Could not bind
            
        self.port_bound.emit(port)
        server.listen(5)
        
        while True:
            client, addr = server.accept()
            buffer = self._receive_message(client)
            if buffer:
                self._handle_payload(buffer, addr)
            client.close()

class FileSenderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, target_ip, target_port, filepath):
        super().__init__()
        self.target_ip = target_ip
        self.target_port = target_port
        self.filepath = filepath
        
    def run(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((self.target_ip, self.target_port))
            
            size = os.path.getsize(self.filepath)
            sent = 0
            with open(self.filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    client.sendall(chunk)
                    sent += len(chunk)
                    if size > 0:
                        self.progress.emit(int((sent / size) * 100))
            client.close()
            self.finished.emit(True)
        except Exception as e:
            print("File send error:", e)
            self.finished.emit(False)

class FileReceiverThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, bytes) # success, filename, data
    
    def __init__(self, port, filename, expected_size, save_path=None):
        super().__init__()
        self.port = port
        self.filename = filename
        self.save_path = save_path
        self.expected_size = expected_size
        
    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(10)
        try:
            server.bind(('0.0.0.0', self.port))
            server.listen(1)
            client, _ = server.accept()
            client.settimeout(5)
            
            received = 0
            
            # Decide where to write: disk or memory
            if self.save_path:
                output = open(self.save_path, 'wb')
            else:
                output = io.BytesIO()

            try:
                while received < self.expected_size:
                    chunk = client.recv(65536)
                    if not chunk:
                        break
                    output.write(chunk)
                    received += len(chunk)
                    if self.expected_size > 0:
                        self.progress.emit(int((received / self.expected_size) * 100))
                
                if isinstance(output, io.BytesIO):
                    self.finished.emit(True, self.filename, output.getvalue())
                else:
                    output.close()
                    self.finished.emit(True, self.filename, b"")
            finally:
                if not isinstance(output, io.BytesIO) and not output.closed:
                    output.close()
            client.close()
        except Exception as e:
            print("File receive error:", e)
            self.finished.emit(False, self.filename, b"")
        finally:
            server.close()


class NotificationBubble(QWidget):
    def __init__(self, title, message):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(240, 90)
        
        layout = QVBoxLayout(self)
        self.frame = QWidget()
        self.frame.setObjectName("bubbleFrame")
        self.frame.setStyleSheet("""
            #bubbleFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(25, 118, 210, 0.2);
                border-radius: 18px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(self.frame)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; color: #1976d2; font-size: 13px;")
        self.msg_label = QLabel(message)
        self.msg_label.setStyleSheet("color: #333; font-size: 12px;")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        frame_layout.addWidget(self.title_label)
        frame_layout.addWidget(self.msg_label)
        layout.addWidget(self.frame)
        
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(600)
        
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(600)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)

    def show_bubble(self, start_pos, end_pos):
        self.move(start_pos)
        self.setWindowOpacity(0)
        self.show()
        
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(end_pos)
        
        self.opacity_anim.start()
        self.pos_anim.start()
        self.timer.start(4500)

    def fade_out(self):
        try:
            self.opacity_anim.stop()
            self.opacity_anim.setStartValue(self.windowOpacity())
            self.opacity_anim.setEndValue(0)
            try:
                self.opacity_anim.finished.disconnect()
            except Exception:
                pass
            self.opacity_anim.finished.connect(self.close)
            self.opacity_anim.start()
        except Exception:
            self.close()

class NotificationManager:
    def __init__(self):
        self.active_bubbles = []
        
    def show_notification(self, title, message):
        bubble = NotificationBubble(title, message)
        self.active_bubbles.append(bubble)
        
        screen = QApplication.primaryScreen().availableGeometry()
        # Stack from bottom-right
        margin = 20
        bubble_height = 95
        x = screen.x() + screen.width() - 250 - margin
        
        # Calculate Y based on current bubbles
        idx = len(self.active_bubbles) - 1
        y = screen.y() + screen.height() - (idx + 1) * bubble_height - margin
        
        if y < screen.y() + margin:
            # Shift or clear if too many
            y = screen.y() + screen.height() - bubble_height - margin
            
        start_pos = QPoint(screen.x() + screen.width(), y)
        end_pos = QPoint(x, y)
        
        bubble.show_bubble(start_pos, end_pos)
        # Use a lambda that safely handles the removal
        bubble.destroyed.connect(lambda: self.on_bubble_destroyed(bubble))

    def on_bubble_destroyed(self, bubble):
        if bubble in self.active_bubbles:
            self.active_bubbles.remove(bubble)

class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(75, 75)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.btn = QPushButton()
        self.btn.setFixedSize(65, 65)
        self.update_style(False)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
        if os.path.exists(icon_path):
            self.btn.setIcon(QIcon(icon_path))
            self.btn.setIconSize(QSize(35, 35))
        else:
            self.btn.setText("OL")
            
        self.btn.clicked.connect(self.restore_main)
        layout.addWidget(self.btn)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 4)
        self.btn.setGraphicsEffect(shadow)
        
        self._drag_pos = None

    def update_style(self, alerting=False):
        color1 = "#ff3d00" if alerting else "#1976d2"
        color2 = "#ff6e40" if alerting else "#42a5f5"
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {color2}, stop:1 {color1});
                border-radius: 32px;
                color: white;
                font-weight: 800;
                font-size: 20px;
                border: 2px solid rgba(255, 255, 255, 0.9);
            }}
            QPushButton:hover {{
                border: 3px solid white;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()
        
    def pulse(self, alerting=True):
        """Create a smooth breathing pulse effect."""
        if alerting:
            self.update_style(True)
            self.pulse_anim = QPropertyAnimation(self, b"windowOpacity")
            self.pulse_anim.setDuration(800)
            self.pulse_anim.setStartValue(1.0)
            self.pulse_anim.setEndValue(0.6)
            self.pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            self.pulse_anim.setLoopCount(6) # Pulse 3 times (down and back)
            self.pulse_anim.finished.connect(lambda: self.update_style(False))
            self.pulse_anim.start()
        else:
            self.update_style(False)

    def restore_main(self):
        self.hide()
        # Restore with expansion animation
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # Trigger restore animation in main window
        self.main_window.animate_restore()

    def position_bottom_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.x() + geom.width() - 90, geom.y() + geom.height() - 90)
        else:
            self.move(800, 800)

# --- MAIN UI ---
class OfficeLink(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OfficeLink LAN")
        self.resize(260, 420)
        
        # Frameless and translucent to enable custom rounded edges
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position towards the right side, vertically centered
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.x() + geom.width() - 280
            y = geom.y() + (geom.height() - 420) // 2
            self.move(x, y)
        else:
            self.move(900, 200)
            
        self.setStyleSheet(STYLESHEET)
        
        self.settings = QSettings("RCNMedia", "OfficeLink")
        self.username = self.settings.value("username", socket.gethostname())
        self.is_mgmt = self.settings.value("is_mgmt", False, type=bool)
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        
        # Enforce management restriction on startup
        if self.username not in ALLOWED_MGMT_USERS:
            self.is_mgmt = False
            self.settings.setValue("is_mgmt", False)
        
        # Load App Icon if available
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Setup System Tray
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.showNormal)
        edit_profile_action = QAction("Edit Profile", self)
        edit_profile_action.triggered.connect(self.edit_profile)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(restore_action)
        tray_menu.addAction(edit_profile_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.pending_files = {}
        self.memory_files = {} # {filename: bytes}
        self.chat_history = [] # List of dicts: {"sender": ..., "msg": ..., "time": ...}
        self.chat_history_lock = threading.Lock()

        self.notif_manager = NotificationManager()
        self.floating_icon = FloatingIcon(self)
        
        # UI Layout
        central = QWidget()
        central.setObjectName("centralFrame")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Username label (click to rename)
        self.username_label = QPushButton(f"👤 {self.username}")
        self.username_label.setObjectName("username_label")
        self.username_label.setToolTip("Click to edit your username")
        self.username_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.username_label.clicked.connect(self.inline_rename)
        controls_layout.addWidget(self.username_label)

        # Management badge (only shown when mgmt mode is on)
        self.mgmt_badge = QLabel("MGMT")
        self.mgmt_badge.setObjectName("mgmt_badge")
        self.mgmt_badge.setVisible(self.is_mgmt)
        controls_layout.addWidget(self.mgmt_badge)

        controls_layout.addStretch()

        # Theme Toggle
        self.theme_btn = QPushButton("🌙" if not self.dark_mode else "☀️")
        self.theme_btn.setObjectName("settings_btn")
        self.theme_btn.setFixedSize(28, 25)
        self.theme_btn.clicked.connect(self.toggle_theme)
        controls_layout.addWidget(self.theme_btn)

        # Settings gear button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("settings_btn")
        self.settings_btn.setFixedSize(28, 25)
        self.settings_btn.setToolTip("Settings / Edit Profile")
        self.settings_btn.clicked.connect(self.edit_profile)
        
        self.min_btn = QPushButton()
        self.min_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarMinButton))
        self.min_btn.setFixedSize(25, 25)
        self.min_btn.setObjectName("min_btn")
        self.min_btn.clicked.connect(self.custom_minimize)
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarCloseButton))
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setObjectName("close_btn")
        self.close_btn.clicked.connect(self.close)
        
        controls_layout.addWidget(self.settings_btn)
        controls_layout.addWidget(self.min_btn)
        controls_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(controls_layout)
        
        content_layout = QHBoxLayout()
        
        # Sidebar
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 5, 0)
        
        self.staff_list = QListWidget()
        self.staff_list.setToolTip("Online Users")
        self.staff_list.itemSelectionChanged.connect(self.on_selection_changed)
        sidebar_layout.addWidget(self.staff_list)
        content_layout.addWidget(sidebar_widget, 1)
        
        if self.dark_mode:
            self.setStyleSheet(DARK_STYLESHEET)
        
        # Chat Area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        self.display = QTextBrowser()
        self.display.setReadOnly(True)
        self.display.setOpenExternalLinks(False)
        self.display.anchorClicked.connect(self.handle_link)
        
        input_area = QHBoxLayout()
        self.file_btn = QPushButton()
        self.file_btn.setObjectName("file_btn")
        # Try to load SVG icon, fallback to text if not found
        file_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_icon.svg")
        if os.path.exists(file_icon_path):
            self.file_btn.setIcon(QIcon(file_icon_path))
            self.file_btn.setIconSize(QSize(24, 24))
        else:
            self.file_btn.setText("📎")
        self.file_btn.setToolTip("Attach File")
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self.send_chat)
        
        self.broadcast_btn = QPushButton("B")
        self.broadcast_btn.setObjectName("broadcast_btn")
        self.broadcast_btn.setToolTip("Broadcast to All")
        self.broadcast_btn.setVisible(self.is_mgmt)
        self.broadcast_btn.clicked.connect(self.broadcast_chat)
        
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("send_btn")
        send_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "send_icon.svg")
        if os.path.exists(send_icon_path):
            self.send_btn.setIcon(QIcon(send_icon_path))
            self.send_btn.setIconSize(QSize(20, 20))
        else:
            self.send_btn.setText("Send")
        self.send_btn.setToolTip("Send")
        self.send_btn.clicked.connect(self.send_chat)
        
        input_area.addWidget(self.file_btn)
        input_area.addWidget(self.input)
        input_area.addWidget(self.broadcast_btn)
        input_area.addWidget(self.send_btn)
        
        # --- Transfer Status Bar ---
        self.transfer_bar_widget = QWidget()
        self.transfer_bar_widget.setObjectName("transfer_bar_widget")
        transfer_bar_layout = QVBoxLayout(self.transfer_bar_widget)
        transfer_bar_layout.setContentsMargins(6, 4, 6, 4)
        transfer_bar_layout.setSpacing(3)

        top_row = QHBoxLayout()
        self.transfer_status_label = QLabel("Transferring...")
        self.transfer_status_label.setObjectName("transfer_status_label")
        self.transfer_pct_label = QLabel("0%")
        self.transfer_pct_label.setObjectName("transfer_pct_label")
        self.transfer_pct_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_row.addWidget(self.transfer_status_label)
        top_row.addWidget(self.transfer_pct_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)

        transfer_bar_layout.addLayout(top_row)
        transfer_bar_layout.addWidget(self.progress)
        self.transfer_bar_widget.setVisible(False)

        chat_layout.addWidget(self.display)
        chat_layout.addWidget(self.transfer_bar_widget)
        chat_layout.addLayout(input_area)
        content_layout.addWidget(chat_widget, 3)
        
        main_layout.addLayout(content_layout)
        
        # Start Threads
        self.comms = CommsThread()
        self.comms.port_bound.connect(self.on_port_bound)
        self.comms.incoming_chat.connect(self.on_message)
        self.comms.file_requested.connect(self.on_file_request)
        self.comms.file_accepted.connect(self.on_file_accepted)
        self.comms.file_rejected.connect(self.on_file_rejected)
        self.comms.start()
        
        # Connections
        self.file_btn.clicked.connect(self.send_file_init)

        # Drag/Resize state
        self._drag_pos = None
        self._resize_edge = 0 # 1:L, 2:R, 4:T, 8:B
        self.setMouseTracking(True)
        central.setMouseTracking(True)
        
    # --- Drag-to-move & Resize support ---
    def get_resize_edge(self, pos):
        rect = self.rect()
        margin = 6 # Reduced for easier dragging
        edge = 0
        if pos.x() < margin: edge |= 1
        if pos.x() > rect.width() - margin: edge |= 2
        if pos.y() < margin: edge |= 4
        if pos.y() > rect.height() - margin: edge |= 8
        return edge

    def get_cursor_for_edge(self, edge):
        if edge in [5, 10]: return Qt.CursorShape.SizeFDiagCursor # TL, BR
        if edge in [6, 9]: return Qt.CursorShape.SizeBDiagCursor  # TR, BL
        if edge in [1, 2]: return Qt.CursorShape.SizeHorCursor   # L, R
        if edge in [4, 8]: return Qt.CursorShape.SizeVerCursor   # T, B
        return Qt.CursorShape.ArrowCursor

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self._resize_edge = self.get_resize_edge(pos)
            
            if not self._resize_edge:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _handle_resize(self, event):
        global_pos = event.globalPosition().toPoint()
        geom = self.geometry()
        min_w, min_h = 250, 400
        
        if self._resize_edge & 1: # Left
            if geom.right() - global_pos.x() > min_w:
                geom.setLeft(global_pos.x())
        elif self._resize_edge & 2: # Right
            if global_pos.x() - geom.left() > min_w:
                geom.setRight(global_pos.x())
            
        if self._resize_edge & 4: # Top
            if geom.bottom() - global_pos.y() > min_h:
                geom.setTop(global_pos.y())
        elif self._resize_edge & 8: # Bottom
            if global_pos.y() - geom.top() > min_h:
                geom.setBottom(global_pos.y())
        
        self.setGeometry(geom)

    def mouseMoveEvent(self, event):
        pos = event.position()
        
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._resize_edge:
                self._handle_resize(event)
            elif self._drag_pos is not None:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            # Update cursor shape on hover
            self.setCursor(self.get_cursor_for_edge(self.get_resize_edge(pos)))

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_edge = 0
        event.accept()

    def insert_bubble(self, sender, msg, is_self=False, is_broadcast=False):
        time_str = datetime.now().strftime("%H:%M")
        safe_msg = html.escape(msg).replace('\n', '<br>')
        
        # Premium Modern Palette
        my_bg = "#1976d2"
        other_bg = "#ffffff"
        broadcast_bg = "#ff3d00"
        
        font_style = "font-family: 'Segoe UI', sans-serif;"
        
        if is_self:
            bg = broadcast_bg if is_broadcast else my_bg
            bubble_html = f"""
                <div style="margin: 8px 0px;">
                    <table width="100%">
                        <tr>
                            <td width="20%"></td>
                            <td align="right">
                                <div style="background-color: {bg}; color: white; border-radius: 16px; border-bottom-right-radius: 4px; padding: 12px; {font_style}">
                                    <div style="font-size: 10px; font-weight: 700; margin-bottom: 4px; opacity: 0.9;">
                                        {"BROADCAST" if is_broadcast else "YOU"} • {time_str}
                                    </div>
                                    <div style="font-size: 13px; line-height: 1.4;">{safe_msg}</div>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
            """
        else:
            bubble_html = f"""
                <div style="margin: 8px 0px;">
                    <table width="100%">
                        <tr>
                            <td align="left">
                                <div style="background-color: {other_bg}; color: #2d3436; border-radius: 16px; border-bottom-left-radius: 4px; padding: 12px; border: 1px solid rgba(0,0,0,0.06); {font_style}">
                                    <div style="font-size: 10px; font-weight: 700; color: #1976d2; margin-bottom: 4px;">
                                        {sender.upper()} • {time_str}
                                    </div>
                                    <div style="font-size: 13px; line-height: 1.4;">{safe_msg}</div>
                                </div>
                            </td>
                            <td width="20%"></td>
                        </tr>
                    </table>
                </div>
            """
        
        self.display.append("")
        self.display.insertHtml(bubble_html)
        # Smooth scroll to bottom
        self.display.verticalScrollBar().setValue(self.display.verticalScrollBar().maximum())

    def inline_rename(self):
        """Quick inline username rename via a simple input dialog."""
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter your new username:",
            text=self.username
        )
        if ok and new_name.strip() and new_name.strip() != self.username:
            self.username = new_name.strip()
            self.settings.setValue("username", self.username)
            self.username_label.setText(f"👤 {self.username}")
            
            # Auto-disable management if new name is not allowed
            if self.username not in ALLOWED_MGMT_USERS:
                self.is_mgmt = False
                self.settings.setValue("is_mgmt", False)
                self.mgmt_badge.setVisible(False)
                self.broadcast_btn.setVisible(False)
            
            if hasattr(self, 'discovery'):
                self.discovery.update_username(self.username)

    def edit_profile(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QFormLayout(dialog)
        
        name_input = QLineEdit(self.username)
        mgmt_checkbox = QCheckBox("Management Mode  (enables Broadcast button)")
        
        # Restriction logic
        can_be_mgmt = self.username in ALLOWED_MGMT_USERS
        mgmt_checkbox.setEnabled(can_be_mgmt)
        mgmt_checkbox.setChecked(self.is_mgmt if can_be_mgmt else False)
        if not can_be_mgmt:
            mgmt_checkbox.setToolTip("Restricted to management staff only.")
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(dialog.accept)
        
        layout.addRow("Username:", name_input)
        layout.addRow("", mgmt_checkbox)
        layout.addRow(save_btn)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_input.text().strip()
            if new_name and new_name != self.username:
                self.username = new_name
                self.settings.setValue("username", self.username)
                self.username_label.setText(f"👤 {self.username}")
                if hasattr(self, 'discovery'):
                    self.discovery.update_username(self.username)
                    
            self.is_mgmt = mgmt_checkbox.isChecked()
            self.settings.setValue("is_mgmt", self.is_mgmt)
            self.broadcast_btn.setVisible(self.is_mgmt)
            self.mgmt_badge.setVisible(self.is_mgmt)
            
    def custom_minimize(self):
        self._pre_min_geom = self.geometry()
        
        # Parallel animation for smoother feel
        self.min_group = QParallelAnimationGroup()
        
        self.min_anim = QPropertyAnimation(self, b"geometry")
        self.min_anim.setDuration(450)
        
        screen = QApplication.primaryScreen().availableGeometry()
        target_x = screen.x() + screen.width() - 80
        target_y = screen.y() + screen.height() - 80
        target_geom = QRect(target_x, target_y, 40, 40)
        
        self.min_anim.setStartValue(self._pre_min_geom)
        self.min_anim.setEndValue(target_geom)
        self.min_anim.setEasingCurve(QEasingCurve.Type.OutQuint)
        
        self.min_fade = QPropertyAnimation(self, b"windowOpacity")
        self.min_fade.setDuration(400)
        self.min_fade.setStartValue(1.0)
        self.min_fade.setEndValue(0.0)
        
        self.min_group.addAnimation(self.min_anim)
        self.min_group.addAnimation(self.min_fade)
        self.min_group.finished.connect(self._finish_minimize)
        self.min_group.start()

    def _finish_minimize(self):
        self.hide()
        self.setWindowOpacity(1.0)
        self.setGeometry(self._pre_min_geom)
        self.floating_icon.position_bottom_right()
        self.floating_icon.show()
        self.floating_icon.pulse()

    def animate_restore(self):
        self.setWindowOpacity(0.0)
        
        # Use the stored pre-minimize geometry as the target
        target_geom = getattr(self, '_pre_min_geom', self.geometry())
        
        # Start the expansion from wherever the floating bubble head currently is
        bubble_center = self.floating_icon.geometry().center()
        start_geom = QRect(bubble_center.x() - 20, bubble_center.y() - 20, 40, 40)
        
        self.setGeometry(start_geom)
        
        self.res_group = QParallelAnimationGroup()
        
        self.res_anim = QPropertyAnimation(self, b"geometry")
        self.res_anim.setDuration(600)
        self.res_anim.setStartValue(start_geom)
        self.res_anim.setEndValue(target_geom)
        self.res_anim.setEasingCurve(QEasingCurve.Type.OutElastic)
        
        self.res_fade = QPropertyAnimation(self, b"windowOpacity")
        self.res_fade.setDuration(350)
        self.res_fade.setStartValue(0.0)
        self.res_fade.setEndValue(1.0)
        
        self.res_group.addAnimation(self.res_anim)
        self.res_group.addAnimation(self.res_fade)
        self.res_group.start()
        
    def on_port_bound(self, port):
        self.discovery = DiscoveryWorker(port, self.username)
        self.discovery.user_found.connect(self.add_user)
        self.discovery.user_lost.connect(self.remove_user)
        self.discovery.start()
        
class UserItemWidget(QWidget):
    def __init__(self, name, ip_port):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Create a colorful circular avatar based on name
        self.avatar = QLabel(name[0].upper() if name else "?")
        self.avatar.setFixedSize(32, 32)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Generate color based on name hash
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        hue = h % 360
        self.avatar.setStyleSheet(f"""
            background-color: hsv({hue}, 150, 200);
            color: white;
            border-radius: 16px;
            font-weight: bold;
            font-size: 14px;
        """)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-weight: 600; font-size: 13px; color: inherit;")
        self.ip_label = QLabel(ip_port)
        self.ip_label.setStyleSheet("font-size: 10px; color: rgba(0,0,0,0.5);")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.ip_label)
        
        layout.addWidget(self.avatar)
        layout.addLayout(info_layout)
        layout.addStretch()

    def update_selection(self, selected):
        if selected:
            self.ip_label.setStyleSheet("font-size: 10px; color: rgba(255,255,255,0.7);")
        else:
            self.ip_label.setStyleSheet("font-size: 10px; color: rgba(0,0,0,0.5);")

    def add_user(self, name, ip_port):
        display_text = f"{name} ({ip_port})"
        if not self.staff_list.findItems(display_text, Qt.MatchFlag.MatchStartsWith):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, ip_port)
            item.setSizeHint(QSize(0, 50))
            self.staff_list.addItem(item)
            
            widget = UserItemWidget(name, ip_port)
            self.staff_list.setItemWidget(item, widget)
            
    def remove_user(self, name):
        for i in range(self.staff_list.count()):
            widget = self.staff_list.itemWidget(self.staff_list.item(i))
            if widget and widget.name_label.text() == name:
                self.staff_list.takeItem(i)
                break

    def on_selection_changed(self):
        """Update UserItemWidget styling when selection changes."""
        for i in range(self.staff_list.count()):
            item = self.staff_list.item(i)
            widget = self.staff_list.itemWidget(item)
            if widget:
                widget.update_selection(item.isSelected())

    def toggle_theme(self):
        """Toggle between light (glass) and dark (catppuccin-ish) themes."""
        self.dark_mode = not self.dark_mode
        self.settings.setValue("dark_mode", self.dark_mode)
        
        if self.dark_mode:
            self.setStyleSheet(DARK_STYLESHEET)
            self.theme_btn.setText("☀️")
        else:
            self.setStyleSheet(STYLESHEET)
            self.theme_btn.setText("🌙")
        
        # Force a refresh of the staff list widgets to inherit theme colors
        self.on_selection_changed()

    def send_network_message(self, target_ip_port, content, msg_type="chat", extra_data=None):
        ip, port = target_ip_port.split(':')
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2)
            client.connect((ip, int(port)))
            payload_dict = {"type": msg_type, "content": content}
            if extra_data:
                payload_dict.update(extra_data)
            payload = json.dumps(payload_dict)
            client.sendall((payload + '\n').encode())
            client.close()
            return True
        except Exception:
            return False

    def send_chat(self):
        msg = self.input.text().strip()
        if not msg: return
        
        selected = self.staff_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a staff member from the list to message.")
            return
            
        target = selected[0].data(Qt.ItemDataRole.UserRole)
        
        if self.send_network_message(target, msg):
            self.input.clear()
            self.insert_bubble("You", msg, is_self=True)
            target_name = selected[0].text().split()[0]
            self.chat_history.append({"sender": "You", "msg": msg, "target": target_name})
        else:
            QMessageBox.warning(self, "Error", "Failed to send message.")
            
    def broadcast_chat(self):
        msg = self.input.text().strip()
        if not msg: return
        
        broadcast_msg = f"[BROADCAST] {msg}"
        self.input.clear()
        
        for i in range(self.staff_list.count()):
            target = self.staff_list.item(i).data(Qt.ItemDataRole.UserRole)
            self.send_network_message(target, broadcast_msg)
                
        self.insert_bubble("You", msg, is_self=True, is_broadcast=True)
        self.chat_history.append({"sender": "You", "msg": msg, "target": "BROADCAST"})

    def on_message(self, sender_ip, msg):
        # Play Notification Sound
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        # Try to resolve IP back to name
        sender_name = sender_ip
        for i in range(self.staff_list.count()):
            item_text = self.staff_list.item(i).text()
            if sender_ip in item_text:
                sender_name = item_text.split()[0]
                break
                
        self.insert_bubble(sender_name, msg, is_self=False)
        self.chat_history.append({"sender": sender_name, "msg": msg})
        
        # Show Bubble Notification
        self.notif_manager.show_notification(f"Message from {sender_name}", msg)
        
        if not self.isActiveWindow():
            self.tray_icon.showMessage("New Message", f"{sender_name}: {msg}", QSystemTrayIcon.MessageIcon.Information, 3000)
            if self.floating_icon.isVisible():
                self.floating_icon.pulse()
        
    def on_file_request(self, sender_ip, name, size, preview):
        size_mb = round(size/1048576, 2)
        safe_name = html.escape(name)
        
        sender_name = sender_ip
        sender_port = None
        for i in range(self.staff_list.count()):
            item = self.staff_list.item(i)
            if sender_ip in item.text():
                sender_name = item.text().split()[0]
                sender_port = item.data(Qt.ItemDataRole.UserRole).split(':')[1]
                break
                
        # Play Notification Sound
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
                
        msg = f"Incoming file from {sender_name}\n{safe_name} ({size_mb} MB)\n\nAccept?"
        
        if not self.isActiveWindow():
            self.tray_icon.showMessage("File Request", f"{sender_name} wants to send {name}", QSystemTrayIcon.MessageIcon.Information, 3000)
            
        # Show Bubble Notification
        self.notif_manager.show_notification(f"File from {sender_name}", f"Wants to send: {name} ({size_mb} MB)")
            
        reply = QMessageBox.question(self, "File Request", msg)
        if reply == QMessageBox.StandardButton.Yes and sender_port:
            self.display.append(f"<i>Receiving {safe_name} to memory...</i>")
            
            receiver_port = 5060
            bound = False
            temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while not bound and receiver_port <= 5100:
                try:
                    temp_sock.bind(('0.0.0.0', receiver_port))
                    bound = True
                except OSError:
                    receiver_port += 1
            temp_sock.close()
            
            self.receiver_thread = FileReceiverThread(receiver_port, name, size)
            self.receiver_thread.progress.connect(self.update_progress)
            self.receiver_thread.finished.connect(self.on_file_received)
            self.show_transfer_bar(f"⬇  Receiving: {safe_name} (RAM)")
            self.receiver_thread.start()
            
            self.send_network_message(f"{sender_ip}:{sender_port}", "", msg_type="file_accept", extra_data={"port": receiver_port})
        elif sender_port:
            self.send_network_message(f"{sender_ip}:{sender_port}", "", msg_type="file_reject")

    def on_file_accepted(self, sender_ip, port):
        if sender_ip in self.pending_files:
            file_path = self.pending_files.pop(sender_ip)
            self.display.append(f"<i>Sending {os.path.basename(file_path)}...</i>")
            self.sender_thread = FileSenderThread(sender_ip, port, file_path)
            self.sender_thread.progress.connect(self.update_progress)
            self.sender_thread.finished.connect(self.on_file_sent)
            self.show_transfer_bar(f"⬆  Sending: {os.path.basename(file_path)}")
            self.sender_thread.start()

    def on_file_rejected(self, sender_ip):
        if sender_ip in self.pending_files:
            file_path = self.pending_files.pop(sender_ip)
            self.display.append(f"<i style='color:red;'>File {os.path.basename(file_path)} was rejected.</i>")

    def show_transfer_bar(self, label_text):
        self.progress.setProperty("complete", False)
        self.progress.style().unpolish(self.progress)
        self.progress.style().polish(self.progress)
        self.progress.setValue(0)
        self.transfer_status_label.setText(label_text)
        self.transfer_pct_label.setText("0%")
        self.transfer_bar_widget.setVisible(True)

    def hide_transfer_bar(self):
        self.transfer_bar_widget.setVisible(False)
        self.progress.setValue(0)

    def update_progress(self, val):
        self.progress.setValue(val)
        self.transfer_pct_label.setText(f"{val}%")

    def on_file_sent(self, success):
        if success:
            self.progress.setProperty("complete", True)
            self.progress.style().unpolish(self.progress)
            self.progress.style().polish(self.progress)
            self.progress.setValue(100)
            self.transfer_pct_label.setText("100%")
            self.transfer_status_label.setText("✓  Sent successfully")
            self.display.append("<i>File sent successfully.</i>")
        else:
            self.transfer_status_label.setText("✗  Send failed")
            self.display.append("<i style='color:red;'>File send failed.</i>")
        QApplication.instance().processEvents()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2500, self.hide_transfer_bar)

    def on_file_received(self, success, filename, data):
        if success:
            self.memory_files[filename] = data
            self.progress.setProperty("complete", True)
            self.progress.style().unpolish(self.progress)
            self.progress.style().polish(self.progress)
            self.progress.setValue(100)
            self.transfer_pct_label.setText("100%")
            self.transfer_status_label.setText("✓  Stored in memory")
            
            safe_name = html.escape(filename)
            self.display.append(f"<i>File {safe_name} received and kept in memory.</i>")
            self.display.insertHtml(f"<a href='save:{safe_name}'>[Save to Disk]</a><br>")
        else:
            self.transfer_status_label.setText("✗  Receive failed")
            self.display.append("<i style='color:red;'>File receive failed.</i>")
        QApplication.instance().processEvents()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2500, self.hide_transfer_bar)

    def handle_link(self, url):
        link = url.toString()
        if link.startswith("save:"):
            filename = link[5:]
            self.save_file_from_memory(filename)

    def save_file_from_memory(self, filename):
        if filename not in self.memory_files:
            QMessageBox.warning(self, "Error", "File not found in memory.")
            return
            
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        default_path = os.path.join(default_dir, filename)
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_path)
        if save_path:
            try:
                with open(save_path, 'wb') as f:
                    f.write(self.memory_files[filename])
                QMessageBox.information(self, "Success", f"File saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
                
    def send_file_init(self):
        selected = self.staff_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a staff member to send a file to.")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            target = selected[0].data(Qt.ItemDataRole.UserRole)
            ip, _ = target.split(':')
            self.pending_files[ip] = file_path
            
            safe_name = html.escape(os.path.basename(file_path))
            size = os.path.getsize(file_path)
            self.display.append(f"<i>Requesting to send {safe_name}...</i>")
            
            self.send_network_message(target, "", msg_type="file_req", extra_data={"filename": os.path.basename(file_path), "size": size})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OfficeLink()
    window.show()
    sys.exit(app.exec())
