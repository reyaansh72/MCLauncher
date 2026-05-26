# MCLauncher

> ⚠️ **Hobby project** — not the most polished launcher out there, but it works and gets the job done. Built for fun and learning.

A lightweight Minecraft launcher built with **Python** and **PySide6**. MCLauncher talks directly to the official Mojang version manifest and handles full game installation — libraries, client jars, Java selection, and local config management.

Supports Minecraft **1.3 → 1.21.11+ stable releases**, with configurable Java rules for newer and experimental versions.

> 🐧 **Linux only.** Windows and macOS are not supported.

---

## 🧠 Project Architecture

| File | Role |
|------|------|
| `app.py` | Main UI, download system, and game execution logic |
| `config.json` | Stores user settings (username, version, RAM) |
| `java_rules.txt` | Java version mapping per Minecraft version |

---

## ⚙️ Features

- 📦 Automatic version list from Mojang manifest
- 📚 Full library download system
- ☕ Automatic Java selection per version
- 🚀 Offline/legacy game launch support
- 💾 Persistent configuration saving
- 📊 Download progress tracking
- 🖥️ PySide6-based UI with animations and drop shadows

---

## 🐧 Binary Release (Linux)

Pre-built binaries are available on the [Releases](../../releases) page.

**Requirements:**
- Linux (x86_64)
- Python 3.14 runtime installed and available on your system

**Run:**

```bash
chmod +x MCLauncher
./MCLauncher
```

No venv, no pip, no setup.

---

## 🔨 Build from Source

### Requirements

- Linux
- Python 3.14+

### Dependencies

**Standard library** (built-in, no install needed):

`sys` `os` `json` `subprocess` `tarfile` `shutil` `threading` `zipfile`

**Third-party** (install via pip):

| Package | Install |
|---------|---------|
| `requests` | `pip install requests` |
| `PySide6` | `pip install PySide6` |

PySide6 modules used: `QtCore`, `QtWidgets`, `QtGui`

```
QtCore   — Qt, QThread, Signal, Property, QEasingCurve, QPropertyAnimation
QtWidgets — QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QComboBox, QPushButton, QProgressBar,
            QTextEdit, QGraphicsDropShadowEffect
QtGui    — QFont, QColor, QPalette
```

### Steps

**1. Clone and enter the project directory**

```bash
git clone <repo-url>
cd MyFirstProjectNoAi
```

**2. Create a virtual environment**

```bash
python3.14 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install requests PySide6
```

**4. Run**

```bash
python app.py
```

---

## 📁 Project Structure

```
MyFirstProjectNoAi/
├── app.py
├── config.json
├── java_rules.txt
├── minecraft/        (auto-generated on first launch)
└── venv/
```

---

## ☕ Java Version Compatibility

MCLauncher supports Minecraft from **1.3 up to 1.21.11+ stable releases**.

Java requirements change as Minecraft evolves — starting with Java Edition 26.1+, Java 25 is required.

Official reference: https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1

### Compatibility Table

| Status | Minecraft Version | Required Java |
|--------|-------------------|---------------|
| ✅ Stable | 1.3 → 1.16 | Java 8 |
| ✅ Stable | 1.17 → 1.20.x | Java 17 |
| ✅ Stable | 1.21 → 1.21.11 | Java 21 |
| ⚠️ Experimental | 1.21.11+ (future builds) | Java 25 or newer |
| ❌ Manual config needed | Above 1.21.11 | Update `java_rules.txt` manually |

---

## 🔧 Java Rules System

`java_rules.txt` controls which Java version is used for each Minecraft version range.

**Format:**

```
# max_version|java_version|download_url
1.16|8|<Java 8 URL>
1.20|17|<Java 17 URL>
1.21.11|21|<Java 21 URL>
26.1|25|<Java 25 URL>
999|25|<experimental / latest builds>
```

---

## 🧠 Advanced Notes

- Java requirements can change between Minecraft releases without warning
- If a version fails to launch, tweak `java_rules.txt` to adjust the Java mapping
- Experimental builds may require newer Java earlier than stable releases
- Java selection is fully configurable — you're in control
