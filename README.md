# MCLauncher

A lightweight, high-performance Minecraft launcher built with Python and Tkinter.

MCLauncher directly uses the official Mojang version manifest and handles full game installation, including libraries, client jars, Java selection, and local configuration management.

It supports Minecraft versions from **1.3 up to 1.21.11+ stable releases**, with configurable Java rules for newer and experimental versions.

---

## 🧠 Project Architecture

The launcher is built around three core files:

- `app.py` — Main UI, download system, and game execution logic  
- `config.json` — Stores user settings (username, version, RAM)  
- `java_rules.txt` — Defines Java version mapping per Minecraft version  

---

## ⚙️ Features

- 📦 Automatic version list from Mojang manifest  
- 📚 Full library download system  
- ☕ Automatic Java selection per version  
- 🚀 Offline/legacy game launch support  
- 💾 Persistent configuration saving  
- 📊 Download progress tracking  
- 🖥️ Clean Tkinter-based UI  

---

## 🛠️ Setup

### 1. Enter project directory

```bash
cd MyFirstProjectNoAi
2. Create virtual environment
python -m venv venv
source venv/bin/activate
3. Install dependencies
pip install requests
▶️ Run Launcher
python app.py
📁 Project Structure
MyFirstProjectNoAi/
├── app.py
├── config.json
├── java_rules.txt
├── minecraft/        (auto-generated)
└── venv/
☕ Java Version Compatibility

MCLauncher supports Minecraft versions from 1.3 up to 1.21.11+ stable releases.

Minecraft’s runtime requirements evolve over time. Starting with Minecraft Java Edition 26.1+, Java 25 is required due to internal system and engine updates.
Official reference:
https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1

⚠️ Compatibility Table
✔ Minecraft 1.3 → 1.16 → Java 8
✔ Minecraft 1.17 → 1.20.x → Java 17
✔ Minecraft 1.21 → 1.21.11 → Java 21 (recommended stable support)
⚠ Minecraft 1.21.11+ (future / experimental builds) → may require Java 25 or newer
❌ Versions above 1.21.11 may require manual Java rule updates
🔧 Java Rules System

java_rules.txt defines which Java version is used per Minecraft version.

Format:
# max_version|java_version|download_url

1.16|8|<Java 8 URL>
1.20|17|<Java 17 URL>
1.21.11|21|<Java 21 URL>
26.1|25|<Java 25 URL (future support)>
999|25|<latest experimental builds>
🧠 Notes for Advanced Users
New Minecraft versions may change Java requirements without warning
If a version fails to launch, adjust java_rules.txt manually
Experimental builds may require newer Java versions earlier than stable releases
Java selection is fully configurable per version rule
