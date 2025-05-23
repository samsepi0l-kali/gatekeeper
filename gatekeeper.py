import sys
import os
import uuid
import pandas as pd
import qrcode
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QFileDialog, QMessageBox, QTextEdit, QHBoxLayout, QComboBox,
    QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QFontDatabase, QFont
import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

class EventQRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Event QR Code Manager")
        self.resize(1200, 700)
        self.setAttribute(Qt.WA_StyledBackground, True)

        font_id = QFontDatabase.addApplicationFont("Orbitron-Regular.ttf")
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(family)
            QApplication.setFont(custom_font)

        self.df = None
        self.loaded_csv_path = None
        self.qrcode_dir = "qrcodes"
        os.makedirs(self.qrcode_dir, exist_ok=True)
        self.scanned_qr_codes = set()

        self.setStyleSheet(
            """
            EventQRApp {
                background-image: url('background.jpg');
                background-repeat: no-repeat;
                background-position: center;
            }
            * {
                color: white;
                font-family: 'Orbitron', 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #7b2cbf;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9d4edd;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid #9d4edd;
                border-radius: 5px;
                padding: 6px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2f;
                color: white;
                selection-background-color: #9d4edd;
            }
            QTextEdit[readOnly="true"] {
                background-color: rgba(0, 0, 0, 0.3);
            }
            QLabel#cameraPreview {
                background-color: black;
                border: 2px solid #9d4edd;
                border-radius: 6px;
            }
            QMenu {
                background-color: #1e1e2f;
                color: white;
                border: 1px solid #9d4edd;
            }
            QMenu::item:selected{
                background-color: #9d4edd;
                color: black;
            }
            """
        )

        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)

        self.generate_btn = QPushButton("Generate QR Codes")
        self.generate_btn.clicked.connect(self.generate_qr_codes)
        self.generate_btn.setEnabled(False)

        self.export_btn = QPushButton("Export List w/ QR & Scan")
        self.export_btn.clicked.connect(self.export_list)
        self.export_btn.setEnabled(False)

        self.reset_btn = QPushButton("Reset Count")
        self.reset_btn.clicked.connect(self.reset_count)
        self.reset_btn.setEnabled(False)

        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.clicked.connect(self.start_camera_scan)
        self.scan_btn.setEnabled(False)

        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.clicked.connect(self.stop_camera_scan)
        self.stop_btn.setEnabled(False)

        self.logo_label = QLabel()
        if os.path.exists("logo.png"):
            self.logo_label.setPixmap(QPixmap("logo.png").scaledToWidth(100, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.camera_selector = QComboBox()
        self.populate_camera_devices()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Passport # …")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_participant)

        self.info_label = QLabel("Load a CSV to get started.")
        self.info_label.setWordWrap(True)
        self.counter_label = QLabel("Scanned: 0 / 0")

        self.camera_label = QLabel(objectName="cameraPreview")
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFixedHeight(120)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(self.logo_label)

        file_layout = QHBoxLayout()
        file_layout.setSpacing(12)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.generate_btn)
        file_layout.addWidget(self.export_btn)
        file_layout.addWidget(self.reset_btn)

        scan_controls = QHBoxLayout()
        scan_controls.setSpacing(12)
        scan_controls.addWidget(QLabel("Camera:"))
        scan_controls.addWidget(self.camera_selector)
        scan_controls.addWidget(self.scan_btn)
        scan_controls.addWidget(self.stop_btn)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        camera_group = QVBoxLayout()
        camera_group.setSpacing(6)
        camera_group.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        camera_group.addWidget(self.info_label)
        camera_group.addWidget(self.counter_label)
        camera_group.addWidget(self.result_text)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(file_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(scan_controls)
        main_layout.addSpacing(10)
        main_layout.addLayout(search_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(camera_group)
        main_layout.addStretch()

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.qr_detector = cv2.QRCodeDetector()

    def populate_camera_devices(self):
        self.camera_selector.clear()
        for i in range(6):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.camera_selector.addItem(f"Camera {i}", i)
                cap.release()

    def update_counter(self):
        if self.df is not None:
            scanned_count = self.df['Scanned'].sum()
            total = len(self.df)
            self.counter_label.setText(f"Scanned: {scanned_count} / {total}")

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            self.df = pd.read_csv(file_path)
            self.loaded_csv_path = file_path
            required_cols = {'Name', 'Passport Number', 'Phone Number', 'Email'}
            if not required_cols.issubset(set(self.df.columns)):
                QMessageBox.warning(self, "Invalid CSV", f"CSV must contain columns: {', '.join(required_cols)}")
                self.df = None
                return
            if 'qr_data' not in self.df.columns:
                self.df['qr_data'] = [str(uuid.uuid4()) for _ in range(len(self.df))]
            if 'Scanned' not in self.df.columns:
                self.df['Scanned'] = False
            self.info_label.setText(f"Loaded {len(self.df)} participants.")
            self.generate_btn.setEnabled(True)
            self.export_btn.setEnabled(False)
            self.reset_btn.setEnabled(True)
            self.scan_btn.setEnabled(True)
            self.result_text.clear()
            self.scanned_qr_codes = set(self.df[self.df['Scanned']].qr_data)
            self.update_counter()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV:\n{str(e)}")

    def generate_qr_codes(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load participant data first.")
            return
        try:
            for _, row in self.df.iterrows():
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(row['qr_data'])
                qr.make(fit=True)
                qr_img = qr.make_image(fill='black', back_color='white')
                filename = f"{row['Name'].replace(' ', '_')}_{row['Passport Number']}.png"
                filepath = os.path.join(self.qrcode_dir, filename)
                qr_img.save(filepath)
            self.info_label.setText(f"QR codes generated and saved in '{self.qrcode_dir}' folder.")
            self.export_btn.setEnabled(True)
            self.result_text.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate QR codes:\n{str(e)}")

    def export_list(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load participant data first.")
            return
        try:
            self.df['QR Code Filename'] = self.df.apply(
                lambda row: f"{row['Name'].replace(' ', '_')}_{row['Passport Number']}.png", axis=1)
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Participant List",
                                                       "participant_list_with_qrcodes.csv", "CSV Files (*.csv)")
            if save_path:
                self.df.to_csv(save_path, index=False)
                self.info_label.setText(f"Participant list exported to {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export list:\n{str(e)}")

    def reset_count(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load participant data first.")
            return
        self.scanned_qr_codes.clear()
        self.df['Scanned'] = False
        if self.loaded_csv_path:
            self.df.to_csv(self.loaded_csv_path, index=False)
        self.update_counter()
        self.result_text.clear()
        self.info_label.setText("Scan count reset.")

    def start_camera_scan(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load participant data first.")
            return

        camera_index = self.camera_selector.currentData()
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", f"Cannot open camera {camera_index}")
            return

        self.info_label.setText("Camera started. Scanning for QR codes...")
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.timer.start(30)

    def stop_camera_scan(self):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.camera_label.clear()
        self.info_label.setText("Camera stopped.")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def update_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        h, w = frame.shape[:2]
        crop_size = 400
        x1 = max(0, w//2 - crop_size//2)
        y1 = max(0, h//2 - crop_size//2)
        x2 = min(w, w//2 + crop_size//2)
        y2 = min(h, h//2 + crop_size//2)
        cropped = frame[y1:y2, x1:x2]

        decoded_objects = pyzbar.decode(cropped, symbols=[ZBarSymbol.QRCODE])
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            if qr_data in self.df['qr_data'].values:
                if qr_data not in self.scanned_qr_codes:
                    self.scanned_qr_codes.add(qr_data)
                    self.df.loc[self.df['qr_data'] == qr_data, 'Scanned'] = True
                    self.result_text.append(f"Scanned: {qr_data}")
                    self.update_counter()
                    if self.loaded_csv_path:
                        self.df.to_csv(self.loaded_csv_path, index=False)
                else:
                    self.result_text.append(f"Already scanned: {qr_data}")
            else:
                self.result_text.append(f"Unknown QR code: {qr_data}")

            # Draw rectangle around QR code
            pts = obj.polygon
            pts = [(pt.x + x1, pt.y + y1) for pt in pts]
            for i in range(len(pts)):
                cv2.line(frame, pts[i], pts[(i+1) % len(pts)], (0, 255, 0), 3)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(q_img).scaled(self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio)
        self.camera_label.setPixmap(pix)

    def search_participant(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load participant data first.")
            return
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.information(self, "Input Needed", "Enter a Passport # to search.")
            return
        filtered = self.df[self.df['Passport Number'].astype(str).str.contains(query)]
        if filtered.empty:
            self.result_text.setText("No participant found.")
        else:
            output = []
            for _, row in filtered.iterrows():
                status = "Scanned" if row['Scanned'] else "Not scanned"
                output.append(f"Name: {row['Name']}\nPassport #: {row['Passport Number']}\nPhone: {row['Phone Number']}\nEmail: {row['Email']}\nStatus: {status}\n---")
            self.result_text.setText("\n".join(output))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EventQRApp()
    window.show()
    sys.exit(app.exec_())
