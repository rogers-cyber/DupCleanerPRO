# DupCleaner PRO v1.0.0 – Professional Duplicate File Finder & Cleaner (Full Source Code)

DupCleaner PRO v1.0.0 is a powerful Python desktop application for finding, previewing, and safely deleting duplicate files.  
This repository contains the **full source code**, allowing you to customize scanning algorithms, UI behavior, deletion rules, thumbnail previews, and export features for your personal or professional file management needs.

------------------------------------------------------------
   🌟 SCREENSHOT
------------------------------------------------------------

<img alt="DupCleaner PRO Main Interface" scr="https://github.com/rogers-cyber/DupCleanerPRO/blob/main/DupCleaner%20PRO.jpg" />

------------------------------------------------------------
🌟 FEATURES
------------------------------------------------------------

- 🔍 Duplicate Detection — Heuristic scanning based on file size and hash
- 📁 Add Files & Folders — Scan single files or entire directories
- 🖼️ Scrollable Thumbnails — Preview image duplicates (PNG, JPG, GIF, BMP)
- 🎯 Keep Newest / First Option — Automatically preserve the newest or first file in each duplicate group
- 🗂️ Grouped Results — View duplicates in organized groups with counts
- ✅ Safe Deletion — Move duplicates to Recycle Bin with confirmation
- 🛑 Stop Control — Safely interrupt ongoing scans
- 📊 Real-Time Progress — Progress bar with ETA and files-per-second speed
- 🧵 Multithreaded Scanning — Responsive UI during large scans
- 📜 Export Results — Save duplicate lists to JSON or TXT
- 🎨 Modern Dark UI — Built with Tkinter + ttkbootstrap
- ⚙️ Fully Customizable — Modify hash algorithm, thumbnail sizes, deletion rules, or UI behavior
- 📘 Built-In About / Help — Usage instructions and feature overview included

------------------------------------------------------------
🚀 INSTALLATION
------------------------------------------------------------

1. Clone or download this repository:

```
git clone https://github.com/rogers-cyber/DupCleanerPRO.git
cd DupCleanerPRO
```

2. Install required Python packages:

```
pip install ttkbootstrap pillow send2trash
```

(Tkinter is included with standard Python installations.)

3. Run the application:

```
python DupCleanerPRO.py
```

4. Optional: Build a standalone executable using PyInstaller:

```
pyinstaller --onefile --windowed DupCleanerPRO.py
```

------------------------------------------------------------
💡 USAGE
------------------------------------------------------------

1. Add Target Files / Folders:
   - Click 📁 **Add Folder** to scan a directory
   - Click 📄 **Add File** to scan individual files
   - Remove selected targets using ❌ **Remove Selected**

2. Configure Options:
   - Enable **Keep Newest File** to automatically preserve the newest file in each duplicate group

3. Scan for Duplicates:
   - Click 🔍 **SCAN DUPLICATES**
   - Monitor progress with ETA and speed indicators
   - Stop scan safely with 🛑 **STOP**

4. Review Duplicate Groups:
   - Click a group to preview files
   - Images are shown as scrollable thumbnails; non-image files as checkboxes

5. Delete Duplicates:
   - Click 🗑️ **DELETE DUPLICATES**
   - Confirm deletion in the custom popup
   - Skipped or failed files are reported

6. Export Results:
   - Click 📃 **TXT** or 🧾 **JSON** to save duplicate lists

7. Help / About:
   - Click ℹ **About / Help** for instructions and tool info

------------------------------------------------------------
⚙️ CONFIGURATION OPTIONS
------------------------------------------------------------

Option                    Description
------------------------- --------------------------------------------------
Target Files/Folders      Files or directories to scan
Keep Newest File          Preserve the newest file in each duplicate group
Start Scan                Begin duplicate detection
Stop Scan                 Interrupt scan safely
Delete Duplicates         Move duplicates to Recycle Bin or permanently delete
Preview Duplicates        Thumbnails for images, list for other files
Export JSON/TXT           Save duplicate reports
About / Help              Usage instructions and overview

------------------------------------------------------------
📦 OUTPUT FORMATS
------------------------------------------------------------

- JSON — Structured duplicate report with group info, file paths, and metadata
- TXT — Human-readable duplicate report, grouped by duplicate sets

------------------------------------------------------------
📦 DEPENDENCIES
------------------------------------------------------------

- Python 3.10+
- ttkbootstrap — Modern themed UI
- Pillow (PIL) — Image processing for thumbnails
- send2trash — Safe Recycle Bin deletion
- Tkinter — Standard Python GUI framework
- Threading — Background scan execution
- OS / Hashlib — File system operations and hashing

------------------------------------------------------------
📝 NOTES
------------------------------------------------------------

- Non-image files are previewed as checkboxes
- Office temporary files (starting with `~$`) are skipped automatically
- Large folders may take longer depending on file count
- Full source code is editable and extensible
- Safe deletion via Recycle Bin is preferred; fallback to permanent delete if necessary

------------------------------------------------------------
👤 ABOUT
------------------------------------------------------------

DupCleaner PRO v1.0.0 is maintained by **MateTools**, providing practical Python-based file management utilities.

Website: https://matetools.gumroad.com

------------------------------------------------------------
📜 LICENSE
------------------------------------------------------------

Distributed as commercial source code.  
You may use it for personal or commercial projects.  
Redistribution, resale, or rebranding as a competing product is **not allowed**.


