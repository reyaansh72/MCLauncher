import sys
import os
import json
import requests
import subprocess
import tarfile
import shutil
import threading
import zipfile

# PySide6 Core UI imports
from PySide6.QtCore import Qt, QThread, Signal, Property, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QProgressBar, QTextEdit, QGraphicsDropShadowEffect)
from PySide6.QtGui import QFont, QColor, QPalette

# =========================
# CONFIG
# =========================
MINECRAFT_FOLDER = "minecraft"
CONFIG_FILE = "config.json"
JAVA_RULES = "java_rules.txt"
JAVA_FOLDER = os.path.join(MINECRAFT_FOLDER, "java")

# =========================
# BACKGROUND WORKER THREADS
# =========================
class VersionLoaderThread(QThread):
    versions_loaded = Signal(list)
    log_signal = Signal(str)

    def run(self):
        self.log_signal.emit("Loading available application indices from Mojang...")
        try:
            url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
            response = requests.get(url, timeout=10)
            data = response.json()
            versions = data.get("versions", [])
            
            version_names = []
            for v in versions:
                vid = v["id"]
                if vid.startswith(("inf", "a", "b", "c", "rd", "pre", "w", "1.14-")):
                    continue
                try:
                    parts = [int(x) for x in vid.split(".") if x.isdigit()]
                    if len(parts) >= 2 and parts[0] == 1 and parts[1] < 3:
                        continue  
                except ValueError:
                    continue
                version_names.append(vid)
            
            self.versions_loaded.emit(version_names)
        except Exception as e:
            self.log_signal.emit(f"Unable to safely communicate with asset servers: {e}")


class LaunchPipelineThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()

    def __init__(self, username, version, ram):
        super().__init__()
        self.username = username
        self.version = version
        self.ram = ram

    def run(self):
        if not self.username:
            self.log_signal.emit("Launch canceled: A username parameter must be specified.")
            self.finished_signal.emit()
            return

        version_json = self.download_version(self.version)
        if version_json is None:
            self.log_signal.emit("Environment deployment terminated due to setup anomalies.")
            self.finished_signal.emit()
            return

        self.log_signal.emit("Scanning runtime dependencies maps...")
        java_data = self.get_java_rule(self.version)
        java_path = self.download_java(java_data[0], java_data[1])
        
        if not java_path:
            self.log_signal.emit("Initialization pipeline dropped.")
            self.finished_signal.emit()
            return

        jars = []
        libraries = version_json.get("libraries", [])
        for library in libraries:
            downloads = library.get("downloads", {})
            artifact = downloads.get("artifact")
            if not artifact:
                continue
            full_path = os.path.join(MINECRAFT_FOLDER, "libraries", artifact.get("path"))
            if os.path.exists(full_path):
                jars.append(full_path)

        client_jar = os.path.join(MINECRAFT_FOLDER, "versions", self.version, f"{self.version}.jar")
        if os.path.exists(client_jar):
            jars.append(client_jar)

        classpath = os.path.pathsep.join(jars)
        main_class = version_json.get("mainClass", "net.minecraft.client.main.Main")
        natives_path = os.path.abspath(os.path.join(MINECRAFT_FOLDER, "versions", self.version, "natives"))

        command = [
            java_path,
            f"-Xmx{self.ram}",
            f"-Djava.library.path={natives_path}",
            f"-Dorg.lwjgl.librarypath={natives_path}",
            "-cp", classpath,
            main_class,
            "--username", self.username,
            "--version", self.version,
            "--gameDir", MINECRAFT_FOLDER,
            "--assetsDir", os.path.join(MINECRAFT_FOLDER, "assets"),
            "--assetIndex", version_json.get("assets", self.version),
            "--accessToken", "0",
            "--userType", "legacy"
        ]

        self.log_signal.emit("Spawning client sandbox pipeline sub-process context.")
        try:
            subprocess.Popen(command, cwd=os.getcwd())
            self.log_signal.emit("Minecraft is running active! Safe to clean up launcher console.")
        except Exception as e:
            self.log_signal.emit(f"Subprocess wrapper failed tracking execution context: {e}")
            
        self.finished_signal.emit()

    def download_version(self, version_id):
        self.log_signal.emit(f"Validating system build metadata profile for {version_id}...")
        try:
            manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
            manifest_data = requests.get(manifest_url).json()
            version_url = next((v["url"] for v in manifest_data["versions"] if v["id"] == version_id), None)
            if not version_url:
                return None

            version_json = requests.get(version_url).json()
            version_frame_folder = os.path.join(MINECRAFT_FOLDER, "versions", version_id)
            natives_folder = os.path.join(version_frame_folder, "natives")
            os.makedirs(natives_folder, exist_ok=True)

            with open(os.path.join(version_frame_folder, f"{version_id}.json"), "w") as file:
                json.dump(version_json, file, indent=4)

            client_url = version_json["downloads"]["client"]["url"]
            jar_path = os.path.join(version_frame_folder, f"{version_id}.jar")
            if not os.path.exists(jar_path):
                self.log_signal.emit("Downloading engine base instance executable...")
                response = requests.get(client_url)
                with open(jar_path, "wb") as file:
                    file.write(response.content)

            libraries = version_json.get("libraries", [])
            total = len(libraries)
            
            self.log_signal.emit("Resolving remote software components and system natives...")
            for current, library in enumerate(libraries, 1):
                percent = (current / total) * 100
                self.progress_signal.emit(percent)

                downloads = library.get("downloads", {})
                is_native = "natives" in library
                native_classifier = None
                if is_native:
                    os_key = "linux" if os.name != "nt" else "windows"
                    native_classifier = library["natives"].get(os_key)

                if native_classifier and "classifiers" in downloads:
                    artifact = downloads["classifiers"].get(native_classifier)
                else:
                    artifact = downloads.get("artifact")

                if not artifact:
                    continue

                path = artifact.get("path")
                url = artifact.get("url")
                full_path = os.path.join(MINECRAFT_FOLDER, "libraries", path)

                if not os.path.exists(full_path):
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    try:
                        response = requests.get(url, timeout=15)
                        with open(full_path, "wb") as file:
                            file.write(response.content)
                    except Exception:
                        continue

                if (is_native or "natives" in path) and os.path.exists(full_path):
                    try:
                        if zipfile.is_zipfile(full_path):
                            with zipfile.ZipFile(full_path, 'r') as zip_ref:
                                for file_info in zip_ref.infolist():
                                    filename = os.path.basename(file_info.filename)
                                    if filename.endswith(('.so', '.dll', '.dylib', '.a')):
                                        target_path = os.path.join(natives_folder, filename)
                                        with open(target_path, "wb") as f_out:
                                            f_out.write(zip_ref.read(file_info.filename))
                    except Exception:
                        pass

            self.log_signal.emit("Dependencies configuration established.")
            return version_json
        except Exception as e:
            self.log_signal.emit(f"Asset mapping failure event triggered: {e}")
            return None

    def get_java_rule(self, version_id):
        default_java21 = (21, "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.8%2B9/OpenJDK21U-jre_x64_linux_hotspot_21.0.8_9.tar.gz")
        try:
            current_parts = [int(x) for x in version_id.split(".")[:2]]
            current_tuple = tuple(current_parts)
        except Exception:
            return default_java21

        if not os.path.exists(JAVA_RULES):
            with open(JAVA_RULES, "w") as file:
                file.write("1.16|8|https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u462-b08/OpenJDK8U-jre_x64_linux_hotspot_8u462b08.tar.gz\n1.20|17|https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.16%2B8/OpenJDK17U-jre_x64_linux_hotspot_17.0.16_8.tar.gz\n999|21|https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.8%2B9/OpenJDK21U-jre_x64_linux_hotspot_21.0.8_9.tar.gz\n")

        with open(JAVA_RULES, "r") as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            split = line.split("|")
            if len(split) != 3:
                continue
            try:
                max_version_str = split[0]
                max_tuple = (999, 0) if max_version_str == "999" else tuple(int(x) for x in max_version_str.split(".")[:2])
                if current_tuple <= max_tuple:
                    return (int(split[1]), split[2])
            except Exception:
                continue
        return default_java21

    def download_java(self, java_version, url):
        os.makedirs(JAVA_FOLDER, exist_ok=True)
        target_folder = os.path.join(JAVA_FOLDER, f"java{java_version}")
        binary_name = "java.exe" if os.name == "nt" else "bin/java"
        java_binary = os.path.join(target_folder, binary_name)

        if os.path.exists(java_binary):
            self.log_signal.emit(f"Dependencies: Java {java_version} runtime verified.")
            return java_binary

        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)

        archive_path = os.path.join(JAVA_FOLDER, f"java{java_version}.tar.gz")
        self.log_signal.emit(f"Downloading required engine workspace assets (Java {java_version})...")
        
        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            with open(archive_path, "wb") as file:
                shutil.copyfileobj(response.raw, file)

            self.log_signal.emit("Extracting local configuration structures...")
            temp_folder = os.path.join(JAVA_FOLDER, "temp")
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            os.makedirs(temp_folder, exist_ok=True)

            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_folder)

            extracted = os.listdir(temp_folder)
            shutil.move(os.path.join(temp_folder, extracted[0]), target_folder)
            shutil.rmtree(temp_folder)
            os.remove(archive_path)
            
            if os.name != "nt" and os.path.exists(java_binary):
                os.chmod(java_binary, 0o755)

            self.log_signal.emit(f"Java Runtime Environment configured successfully.")
            return java_binary
        except Exception as e:
            self.log_signal.emit(f"Runtime extraction failed: {e}")
            if os.path.exists(target_folder): shutil.rmtree(target_folder)
            return None


# =========================
# ANIMATED GLOWING BUTTON
# =========================
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._color_ratio = 0.0
        
        # Subtle fade-in on startup animation
        self.ani = QPropertyAnimation(self, b"color_ratio")
        self.ani.setDuration(250)
        self.ani.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @Property(float)
    def color_ratio(self):
        return self._color_ratio

    @color_ratio.setter
    def color_ratio(self, val):
        self._color_ratio = val
        # Dynamically interpolate button style sheets over transitions
        bg_color = QColor(0, 122, 204).name() # Normal Blue
        if val > 0:
            # Interpolate towards Hover color (Lighter Blue Cyan)
            bg_color = f"color-mix(in srgb, #0098ff {int(val*100)}%, #007acc)"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                letter-spacing: 1px;
            }}
            QPushButton:disabled {{
                background-color: #2d2d30;
                color: #5a5a5a;
            }}
        """)

    def enterEvent(self, event):
        if self.isEnabled():
            self.ani.stop()
            self.ani.setEndValue(1.0)
            self.ani.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self.ani.stop()
            self.ani.setEndValue(0.0)
            self.ani.start()
        super().leaveEvent(event)


# =========================
# MAIN MODERN UI WINDOW
# =========================
class MCLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MC Launcher")
        self.setMinimumSize(950, 680)
        self.init_ui()
        self.load_local_saved_config()
        
        # Async background thread for Mojang manifest API queries
        self.loader_thread = VersionLoaderThread()
        self.loader_thread.versions_loaded.connect(self.populate_versions)
        self.loader_thread.log_signal.connect(self.append_log)
        self.loader_thread.start()

    def init_ui(self):
        # Master Modern AMOLED Dark Stylesheet Configuration
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0b0c;
            }
            QWidget#CentralWidget {
                background-color: #0b0b0c;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #161618;
                color: #ffffff;
                border: 1px solid #242427;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
                background-color: #1a1a1d;
            }
            QComboBox {
                background-color: #161618;
                color: #ffffff;
                border: 1px solid #242427;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                combobox-popup: 0;
            }
            QComboBox:focus {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
            }
            QComboBox QAbstractItemView {
                background-color: #161618;
                color: #ffffff;
                border: 1px solid #242427;
                selection-background-color: #007acc;
                selection-foreground-color: #ffffff;
            }
            QProgressBar {
                background-color: #161618;
                border: none;
                border-radius: 3px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #111112;
                color: #00ccff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid #1c1c1e;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        # Base Layout architecture structure setup
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(45, 35, 45, 35)
        main_layout.setSpacing(20)

        # Brand Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        self.title_lbl = QLabel("MC LAUNCHER")
        self.title_lbl.setStyleSheet("font-size: 28px; font-weight: 800; letter-spacing: 1px; color: #ffffff;")
        header_layout.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("High Performance Virtualization Sandbox Node")
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #646469; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;")
        header_layout.addWidget(self.sub_lbl)
        main_layout.addLayout(header_layout)

        # Card Container Frame for Interactive Form Widgets
        self.card_widget = QWidget()
        self.card_widget.setStyleSheet("QWidget { background-color: #121214; border-radius: 12px; }")
        
        # Soft modern box shadow drop effect on the interactive card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.card_widget.setGraphicsEffect(shadow)

        card_layout = QHBoxLayout(self.card_widget)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)

        # Form Field 1: Profile Username Input
        u_box = QVBoxLayout()
        u_lbl = QLabel("USERNAME")
        u_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #007acc; letter-spacing: 0.5px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Player Identity String")
        self.username_input.textChanged.connect(self.save_local_current_config)
        u_box.addWidget(u_lbl)
        u_box.addWidget(self.username_input)
        card_layout.addLayout(u_box, stretch=1)

        # Form Field 2: Client Profile Version Combobox Dropdown
        v_box = QVBoxLayout()
        v_lbl = QLabel("MINECRAFT VERSION")
        v_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #007acc; letter-spacing: 0.5px;")
        self.version_dropdown = QComboBox()
        self.version_dropdown.currentIndexChanged.connect(self.save_local_current_config)
        v_box.addWidget(v_lbl)
        v_box.addWidget(self.version_dropdown)
        card_layout.addLayout(v_box, stretch=1)

        # Form Field 3: RAM Heap Memory Allocations Dropdown
        r_box = QVBoxLayout()
        r_lbl = QLabel("ALLOCATED MEMORY")
        r_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #007acc; letter-spacing: 0.5px;")
        self.ram_dropdown = QComboBox()
        self.ram_dropdown.addItems(["2G", "4G", "6G", "8G"])
        self.ram_dropdown.setCurrentIndex(1)
        self.ram_dropdown.currentIndexChanged.connect(self.save_local_current_config)
        r_box.addWidget(r_lbl)
        r_box.addWidget(self.ram_dropdown)
        card_layout.addLayout(r_box, stretch=1)

        main_layout.addWidget(self.card_widget)

        # Progress Linear Track bar Component
        self.p_bar = QProgressBar()
        self.p_bar.setFixedHeight(6)
        self.p_bar.setValue(0)
        main_layout.addWidget(self.p_bar)

        # Centered Layout Section for Modern Button Trigger
        btn_center_layout = QHBoxLayout()
        btn_center_layout.addStretch()
        self.launch_btn = AnimatedButton("LAUNCH GAME")
        self.launch_btn.setFixedSize(240, 52)
        self.launch_btn.clicked.connect(self.trigger_launch_pipeline)
        btn_center_layout.addWidget(self.launch_btn)
        btn_center_layout.addStretch()
        main_layout.addLayout(btn_center_layout)

        # Immersive Output Logs Text Widget Engine
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        main_layout.addWidget(self.log_box)

    # =========================
    # LOGIC WRAPPERS
    # =========================
    def append_log(self, txt):
        self.log_box.append(str(txt))
        self.log_box.ensureCursorVisible()

    def populate_versions(self, version_list):
        self.version_dropdown.blockSignals(True)
        self.version_dropdown.clear()
        self.version_dropdown.addItems(version_list)
        self.version_dropdown.blockSignals(False)
        self.append_log("Version listings mapped successfully.")
        self.load_local_saved_config()

    def save_local_current_config(self):
        data = {
            "username": self.username_input.text().strip(),
            "version": self.version_dropdown.currentText(),
            "ram": self.ram_dropdown.currentText()
        }
        with open(CONFIG_FILE, "w") as file:
            json.dump(data, file, indent=4)

    def load_local_saved_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r") as file:
                data = json.load(file)
            
            self.username_input.blockSignals(True)
            self.version_dropdown.blockSignals(True)
            self.ram_dropdown.blockSignals(True)

            self.username_input.setText(data.get("username", ""))
            self.ram_dropdown.setCurrentText(data.get("ram", "4G"))
            
            saved_ver = data.get("version", "")
            idx = self.version_dropdown.findText(saved_ver)
            if idx != -1:
                self.version_dropdown.setCurrentIndex(idx)

            self.username_input.blockSignals(False)
            self.version_dropdown.blockSignals(False)
            self.ram_dropdown.blockSignals(False)
        except Exception:
            pass

    def trigger_launch_pipeline(self):
        self.launch_btn.setEnabled(False)
        self.launch_btn.setText("LAUNCHING...")
        
        # Spawn isolated execution pipeline loop thread preventing UI thread locking
        self.pipeline_thread = LaunchPipelineThread(
            self.username_input.text().strip(),
            self.version_dropdown.currentText(),
            self.ram_dropdown.currentText()
        )
        self.pipeline_thread.log_signal.connect(self.append_log)
        self.pipeline_thread.progress_signal.connect(self.p_bar.setValue)
        self.pipeline_thread.finished_signal.connect(self.launch_pipeline_ended)
        self.pipeline_thread.start()

    def launch_pipeline_ended(self):
        self.launch_btn.setEnabled(True)
        self.launch_btn.setText("LAUNCH GAME")
        self.p_bar.setValue(0)


# =========================
# APPLICATION EXECUTION ENTRY
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Force platform layout structures to interpret font scales gracefully on High-DPI Linux configurations
    app.setStyle('Fusion')
    
    launcher = MCLauncher()
    launcher.show()
    sys.exit(app.exec())
