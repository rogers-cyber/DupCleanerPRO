"""
DupCleaner PRO v1.0.0
Professional Duplicate File Finder & Cleaner
Scrollable Thumbnails | Auto-Delete | Keep Newest Option
"""

import os, sys, threading, time, json
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
from collections import defaultdict
import hashlib
from send2trash import send2trash

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

# =================== GLOBALS ===================
stop_event = threading.Event()
all_files = set()
duplicates = defaultdict(list)
tree_iid_map = {}  # stable mapping Treeview IID -> file list
thumbnail_cache = []
file_delete_vars = {}  # file path -> BooleanVar

log_file = os.path.join(os.getcwd(), "dupcleaner.log")
settings_file = os.path.join(os.getcwd(), "dupcleaner_settings.json")

# =================== UTIL ===================
def resource_path(file_name):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, file_name)

def file_hash(path, chunk_size=65536, quick=True):
    md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            if quick:
                md5.update(f.read(65536))
            else:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    md5.update(data)
    except Exception:
        return None
    return md5.hexdigest()

def log_error(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def format_size(num):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024

# ---------------------- Helper for consistent messages ----------------------
def _show_message(title, text, msg_type="info"):
    """Custom popup window for messages (info, success, error)."""
    colors = {"info": "#2563eb", "success": "#16a34a", "error": "#dc2626"}  # blue, green, red
    win = tb.Toplevel(app)
    win.title(title)
    win.geometry("420x180")
    win.resizable(False, False)
    win.grab_set()
    win.attributes("-toolwindow", True)

    app.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() // 2) - 210
    y = app.winfo_y() + (app.winfo_height() // 2) - 90
    win.geometry(f"+{x}+{y}")

    frame = tb.Frame(win, padding=15)
    frame.pack(fill="both", expand=True)

    tb.Label(frame, text=title, font=("Segoe UI", 14, "bold"), foreground=colors.get(msg_type, "#000")).pack(pady=(0, 10))
    tb.Label(frame, text=text, font=("Segoe UI", 11), wraplength=380, justify="left").pack(pady=(0, 15))
    tb.Button(frame, text="Close", bootstyle="success-outline", width=12, command=win.destroy).pack(pady=5)

# =================== ROOT ===================
app = tb.Window(themename="darkly")
app.title("DupCleaner PRO")
app.geometry("1200x680")

try:
    app.iconbitmap(resource_path("logo.ico"))
except Exception:
    pass

progress_value = tk.IntVar(app)
keep_newest_var = tk.BooleanVar(value=False)

# =================== TITLE ===================
tb.Label(app, text="DupCleaner PRO", font=("Segoe UI", 22, "bold")).pack(pady=(10, 2))
tb.Label(
    app,
    text="Professional Duplicate File Finder & Cleaner",
    font=("Segoe UI", 10, "italic"),
    foreground="#9ca3af"
).pack(pady=(0, 8))

# =================== TARGET ===================
row1 = tb.Labelframe(app, text="Add Files / Folders", padding=10)
row1.pack(fill="x", padx=10, pady=6)

target_paths = []

listbox_frame = tb.Frame(row1)
listbox_frame.pack(side="left", fill="both", expand=True, padx=6)

target_listbox = tk.Listbox(listbox_frame, height=5, selectmode="extended", width=60)
target_listbox.pack(side="left", fill="both", expand=True)

scrollbar = tb.Scrollbar(listbox_frame, orient="vertical", command=target_listbox.yview)
scrollbar.pack(side="right", fill="y")
target_listbox.config(yscrollcommand=scrollbar.set)

tb.Button(row1, text="📁 Add Folder", bootstyle="secondary", command=lambda: add_folder_ui()).pack(side="left", padx=4)
tb.Button(row1, text="📄 Add File", bootstyle="secondary", command=lambda: add_files_ui()).pack(side="left", padx=4)
tb.Button(row1, text="❌ Remove Selected", bootstyle="danger", command=lambda: remove_selected_ui()).pack(side="left", padx=4)

tb.Checkbutton(row1, text="Keep Newest File in Duplicates", variable=keep_newest_var, bootstyle="info").pack(side="right", padx=6)

# =================== CONTROLS ===================
row2 = tb.Labelframe(app, text="Scan Controls", padding=10)
row2.pack(fill="x", padx=10, pady=6)

start_btn = tb.Button(row2, text="🔍 SCAN DUPLICATES", bootstyle="success")
stop_btn = tb.Button(row2, text="🛑 STOP", bootstyle="danger-outline", state="disabled")
delete_btn = tb.Button(row2, text="🗑️ DELETE DUPLICATES", bootstyle="danger-outline", state="disabled")

start_btn.pack(side="left", padx=6)
stop_btn.pack(side="left", padx=6)
delete_btn.pack(side="left", padx=6)

tb.Button(row2, text="ℹ About / Help", bootstyle="info-outline", command=lambda: show_about()).pack(side="right", padx=4)
tb.Button(row2, text="🧾 JSON", bootstyle="secondary-outline", command=lambda: export_json()).pack(side="right", padx=4)
tb.Button(row2, text="📃 TXT", bootstyle="secondary-outline", command=lambda: export_txt()).pack(side="right", padx=4)

# =================== PROGRESS ===================
row3 = tb.Labelframe(app, text="Progress", padding=8)
row3.pack(fill="x", padx=10)

progress_bar = tb.Progressbar(row3, variable=progress_value, maximum=100, length=520)
progress_bar.pack(side="left", padx=10)

eta_lbl = tb.Label(row3, text="ETA: --")
eta_lbl.pack(side="left", padx=10)

spd_lbl = tb.Label(row3, text="Speed: -- files/s")
spd_lbl.pack(side="left", padx=10)

stats_lbl = tb.Label(row3, text="Files: 0 | Duplicates: 0")
stats_lbl.pack(side="right", padx=10)

# =================== RESULTS ===================
row4 = tb.Labelframe(
    app,
    text="Duplicate Groups – Click a group to preview files",
    padding=10
)
row4.pack(fill="both", expand=True, padx=10, pady=6)

results_frame = tb.Frame(row4)
results_frame.pack(fill="both", expand=True)

# --- LEFT PANEL: Treeview ---
tree_frame = tb.Frame(results_frame)
tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

tree_cols = ("group", "count")
tree = tb.Treeview(tree_frame, columns=tree_cols, show="headings", selectmode="browse")
for col in tree_cols:
    tree.heading(col, text=col.upper())
    tree.column(col, anchor="w")

scroll_y = tb.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
scroll_x = tb.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# --- RIGHT PANEL: Preview ---
preview_frame = tb.Labelframe(results_frame, text="Preview Duplicate Files", padding=5)
preview_frame.pack(side="right", fill="both", expand=True)

# =================== THUMBNAILS / FILE SELECTION ===================
def show_thumbnails(files):
    """Display image thumbnails in a responsive grid inside preview_frame."""
    global thumbnail_cache
    for widget in preview_frame.winfo_children():
        widget.destroy()
    thumbnail_cache.clear()

    if not files:
        return

    # Scrollable canvas
    canvas = tk.Canvas(preview_frame)
    scrollbar = tk.Scrollbar(preview_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Dynamically calculate number of columns based on preview_frame width
    def update_grid(event=None):
        w = scroll_frame.winfo_width() or 600
        thumb_width = 120 + 10  # thumbnail width + padding
        cols = max(1, w // thumb_width)
        for idx, lbl in enumerate(scroll_frame.winfo_children()):
            row = idx // cols
            col = idx % cols
            lbl.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        for c in range(cols):
            scroll_frame.grid_columnconfigure(c, weight=1)

    # Create thumbnails
    for f in files:
        if not f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            continue
        try:
            img = Image.open(f)
            img.thumbnail((120, 120))
            tk_img = ImageTk.PhotoImage(img)
            thumbnail_cache.append(tk_img)
            lbl = tk.Label(scroll_frame, image=tk_img, text=os.path.basename(f), compound="top")
            lbl.bind("<Configure>", update_grid)
            lbl.grid(padx=5, pady=5)
        except Exception as e:
            log_error(f"Thumbnail failed: {f} | {e}")

    # Update grid whenever frame is resized
    scroll_frame.bind("<Configure>", update_grid)

def show_file_selection(files):
    global file_delete_vars
    for widget in preview_frame.winfo_children():
        widget.destroy()
    file_delete_vars.clear()

    if not files:
        return

    for f in files:
        var = tk.BooleanVar(value=True)
        file_delete_vars[f] = var
        cb = tk.Checkbutton(preview_frame, text=os.path.basename(f), variable=var)
        cb.pack(anchor="w", padx=5, pady=2)

# =================== TREE SELECTION ===================
def refresh_tree():
    tree.delete(*tree.get_children())
    tree_iid_map.clear()
    for i, lst in enumerate(duplicates.values(), 1):
        iid = str(id(lst))
        tree.insert("", "end", iid=iid, values=(f"Group {i}", len(lst)))
        tree_iid_map[iid] = lst

def on_group_select(event):
    selected = event.widget.selection()
    if not selected:
        return
    iid = selected[0]
    files = tree_iid_map.get(iid, [])

    if any(f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")) for f in files):
        show_thumbnails(files)
    else:
        show_file_selection(files)

tree.bind("<<TreeviewSelect>>", on_group_select)

# =================== FILE / FOLDER ADDING ===================
def add_files_ui():
    global target_paths, all_files
    files = filedialog.askopenfilenames()
    if files:
        for f in files:
            if f not in target_paths:
                target_paths.append(f)
                all_files.add(f)
                target_listbox.insert("end", f)
        update_stats()

def add_folder_ui():
    global target_paths, all_files
    folder = filedialog.askdirectory()
    if folder:
        if folder not in target_paths:
            target_paths.append(folder)
            target_listbox.insert("end", folder)
            threading.Thread(target=scan_folder_thread, args=(folder,), daemon=True).start()

def remove_selected_ui():
    global target_paths, all_files
    selected_indices = list(target_listbox.curselection())
    selected_indices.reverse()
    for i in selected_indices:
        path = target_listbox.get(i)
        target_listbox.delete(i)
        if os.path.isfile(path):
            all_files.discard(path)
        else:
            all_files = {f for f in all_files if not f.startswith(path)}
        target_paths.remove(path)
    update_stats()

def scan_folder_thread(folder):
    global all_files
    new_files = set()
    for root, _, files in os.walk(folder):
        for f in files:
            new_files.add(os.path.join(root, f))
    all_files.update(new_files)
    app.after(0, update_stats)

# =================== SCAN DUPLICATES ===================
def scan_duplicates():
    if not all_files:
        _show_message("No Files ⚠️", "No files have been added for scanning.\nPlease add files or folders first.", "info")
        return

    stop_event.clear()
    start_btn.config(state="disabled")
    stop_btn.config(state="normal")
    delete_btn.config(state="disabled")
    duplicates.clear()
    tree.delete(*tree.get_children())
    progress_value.set(0)

    threading.Thread(target=scan_duplicates_thread, daemon=True).start()

def scan_duplicates_thread():
    size_map = defaultdict(list)
    files_list = list(all_files)
    processed = 0
    start_time = time.time()

    for f in files_list:
        if stop_event.is_set():
            finish_scan()
            return
        try:
            size_map[os.path.getsize(f)].append(f)
        except Exception:
            continue

    candidate_groups = [g for g in size_map.values() if len(g) > 1]
    if not candidate_groups:
        finish_scan()
        return

    for group in candidate_groups:
        if stop_event.is_set():
            finish_scan()
            return
        quick_map = defaultdict(list)
        for f in group:
            if stop_event.is_set():
                finish_scan()
                return
            h = file_hash(f, quick=True)
            if h:
                quick_map[h].append(f)
            processed += 1
            app.after(0, lambda p=processed: update_progress(p, sum(len(g) for g in candidate_groups), start_time))

        for vals in quick_map.values():
            if len(vals) > 1:
                full_map = defaultdict(list)
                for f in vals:
                    h = file_hash(f, quick=False)
                    if h:
                        full_map[h].append(f)
                for final in full_map.values():
                    if len(final) > 1:
                        duplicates[id(final)] = final

    app.after(0, finish_scan)

def update_progress(processed, total, start_time):
    progress_value.set(int(processed / total * 100))
    elapsed = time.time() - start_time
    spd_lbl.config(text=f"Speed: {processed/elapsed:.1f} files/s" if elapsed else "--")
    eta = int((total-processed)/(processed/elapsed)) if processed else 0
    eta_lbl.config(text=f"ETA: {eta}s")

def finish_scan():
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")
    delete_btn.config(state="normal")
    refresh_tree()
    update_stats()

    total_dupes = sum(len(v) for v in duplicates.values())
    total_groups = len(duplicates)
    total_size = sum(os.path.getsize(f) for group in duplicates.values() for f in group if os.path.exists(f))

    # Create a custom user-friendly window
    win = tb.Toplevel(app)
    win.title("Scan Complete ✅")
    win.geometry("400x280")
    win.resizable(False, False)
    win.grab_set()  # modal window
    win.attributes("-toolwindow", True)

    # Center window relative to main app
    app.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() // 2) - 200
    y = app.winfo_y() + (app.winfo_height() // 2) - 125
    win.geometry(f"+{x}+{y}")

    frame = tb.Frame(win, padding=15)
    frame.pack(fill="both", expand=True)

    # Title
    tb.Label(frame, text="Scan Complete!", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

    # Stats
    tb.Label(frame, text=f"✅ Total Duplicate Files: {total_dupes}", font=("Segoe UI", 12)).pack(anchor="w", pady=4)
    tb.Label(frame, text=f"📂 Duplicate Groups: {total_groups}", font=("Segoe UI", 12)).pack(anchor="w", pady=4)
    tb.Label(frame, text=f"💾 Total Size: {format_size(total_size)}", font=("Segoe UI", 12)).pack(anchor="w", pady=4)

    # Friendly tip
    tb.Label(frame, text="You can review each group on the right panel before deleting duplicates.", 
             font=("Segoe UI", 10), foreground="#6b7280", wraplength=360, justify="left").pack(pady=(10, 5))

    # Close button
    tb.Button(frame, text="Close", bootstyle="success-outline", width=12, command=win.destroy).pack(pady=10)

def update_stats():
    total_dupes = sum(len(v) for v in duplicates.values())
    stats_lbl.config(text=f"Files: {len(all_files)} | Duplicates: {total_dupes}")

def stop_scan():
    stop_event.set()
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")

# =================== DELETE DUPLICATES ===================
def delete_duplicates():
    if not duplicates:
        _show_message("No Duplicates ❌", "No duplicates found to delete.", "info")
        return

    keep_newest = keep_newest_var.get()
    deleted = 0
    total_size = 0
    skipped_files = []
    failed_files = []

    # Gather deletion candidates
    files_to_delete = []
    for lst in duplicates.values():
        if keep_newest:
            lst_sorted = sorted(lst, key=lambda x: os.path.getmtime(x), reverse=True)
            candidates = lst_sorted[1:]
        else:
            candidates = lst[1:]

        for f in candidates:
            if file_delete_vars.get(f, tk.BooleanVar(value=True)).get():
                basename = os.path.basename(f)
                # Skip Office temp files
                if basename.startswith("~$"):
                    skipped_files.append(f)
                    log_error(f"Skipped temp file: {f}")
                    continue
                files_to_delete.append(f)

    if not files_to_delete:
        _show_message(
            "Nothing to Delete ⚠️",
            "No files eligible for deletion. All may be temporary or skipped.",
            "info"
        )
        return

    # Confirmation popup
    total_files_size = sum(os.path.getsize(f) for f in files_to_delete if os.path.exists(f))
    confirm = _confirm_delete(len(files_to_delete), total_files_size, keep_newest)
    if not confirm:
        return

    # Perform deletion
    for f in files_to_delete:
        if not os.path.exists(f):
            skipped_files.append(f)
            log_error(f"Skipped missing file: {f}")
            continue

        try:
            # Normalize path to Windows style
            f_norm = os.path.normpath(os.path.abspath(f))
            send2trash(f_norm)  # Try sending to Recycle Bin
            all_files.discard(f)
            deleted += 1
            try:
                total_size += os.path.getsize(f)
            except Exception:
                pass
        except Exception as e:
            log_error(f"send2trash failed, trying os.remove(): {f} | {e}")
            try:
                os.remove(f_norm)  # Fallback to permanent delete
                all_files.discard(f)
                deleted += 1
                try:
                    total_size += os.path.getsize(f)
                except Exception:
                    pass
            except Exception as e2:
                skipped_files.append(f)
                failed_files.append((f, str(e2)))
                log_error(f"Permanent delete failed: {f} | {e2}")

    # Clear duplicates and refresh UI
    duplicates.clear()
    refresh_tree()
    update_stats()

    # Build user-friendly summary
    summary = f"✅ Deleted {deleted} file{'s' if deleted != 1 else ''}"
    if total_size:
        summary += f" ({format_size(total_size)})"
    if skipped_files:
        summary += f"\n⚠ Skipped {len(skipped_files)} temporary, missing, or locked files"
    if failed_files:
        summary += f"\n❌ Failed to delete {len(failed_files)} files. See log for details."

    # Optional: show first 10 skipped/failed files
    if skipped_files:
        summary += "\n\nFirst skipped files:\n" + "\n".join(os.path.basename(f) for f in skipped_files[:10])
    if failed_files:
        summary += "\n\nFirst failed files:\n" + "\n".join(os.path.basename(f) for f, _ in failed_files[:10])

    _show_message("Deletion Summary 🗑️", summary, "success")

def _confirm_delete(file_count, total_size, keep_newest):
    """Custom confirmation dialog for deletion."""
    confirmed = []

    win = tb.Toplevel(app)
    win.title("Move Files to Recycle Bin ⚠️")
    win.geometry("450x270")
    win.resizable(False, False)
    win.grab_set()
    win.attributes("-toolwindow", True)

    app.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() // 2) - 225
    y = app.winfo_y() + (app.winfo_height() // 2) - 125
    win.geometry(f"+{x}+{y}")

    frame = tb.Frame(win, padding=15)
    frame.pack(fill="both", expand=True)

    tb.Label(frame, text="Confirm Deletion", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
    msg = (
        f"You are about to move {file_count} files ({format_size(total_size)}) to the Recycle Bin.\n\n"
        f"Kept file per group: {'Newest' if keep_newest else 'First'}\n\n"
        "You can restore files later from the Recycle Bin.\n\nProceed?"
    )
    tb.Label(frame, text=msg, font=("Segoe UI", 11), wraplength=410, justify="left").pack(pady=(0, 15))

    def on_confirm():
        confirmed.append(True)
        win.destroy()

    def on_cancel():
        win.destroy()

    btn_frame = tb.Frame(frame)
    btn_frame.pack(pady=5)
    tb.Button(btn_frame, text="Yes, Delete", bootstyle="danger", width=12, command=on_confirm).pack(side="left", padx=10)
    tb.Button(btn_frame, text="Cancel", bootstyle="secondary-outline", width=12, command=on_cancel).pack(side="left", padx=10)

    win.wait_window()
    return bool(confirmed)

# =================== EXPORT ===================
def export_json():
    if not duplicates:
        _show_message("No Data ⚠️", "No duplicates to export.", "info")
        return

    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not path:
        return

    try:
        data = {f"Group {i+1}": lst for i, lst in enumerate(duplicates.values())}
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "tool": "DupCleaner PRO",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "duplicates": data
            }, f, indent=2)
        _show_message("Export Success ✅", f"JSON saved successfully at:\n{path}", "success")
    except Exception as e:
        _show_message("Export Error ❌", f"Failed to save JSON:\n{e}", "error")


def export_txt():
    if not duplicates:
        _show_message("No Data ⚠️", "No duplicates to export.", "info")
        return

    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if not path:
        return

    try:
        with open(path, "w", encoding="utf-8") as f:
            for i, lst in enumerate(duplicates.values(), 1):
                f.write(f"Group {i} ({len(lst)} files)\n")
                for file in lst:
                    f.write(f"{file}\n")
                f.write("\n")
        _show_message("Export Success ✅", f"TXT saved successfully at:\n{path}", "success")
    except Exception as e:
        _show_message("Export Error ❌", f"Failed to save TXT:\n{e}", "error")

# =================== SETTINGS ===================
def load_settings():
    global target_paths
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                data = json.load(f)
            target_paths = data.get("target_paths", [])
            keep_newest_var.set(data.get("keep_newest", False))
            target_listbox.delete(0, "end")
            for path in target_paths:
                target_listbox.insert("end", path)
                if os.path.isfile(path):
                    all_files.add(path)
                else:
                    threading.Thread(target=scan_folder_thread, args=(path,), daemon=True).start()
        except Exception as e:
            log_error(f"Load settings failed: {e}")

def save_settings():
    data = {"target_paths": target_paths, "keep_newest": keep_newest_var.get()}
    try:
        with open(settings_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_error(f"Save settings failed: {e}")

def on_close():
    save_settings()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)
load_settings()

# =================== ABOUT / HELP ===================
def show_about():
    win = tb.Toplevel(app)
    win.title("DupCleaner PRO – About & Help")
    win.geometry("520x570")
    win.resizable(False, False)
    win.grab_set()
    win.attributes("-toolwindow", True)

    app.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() // 2) - 260
    y = app.winfo_y() + (app.winfo_height() // 2) - 285
    win.geometry(f"+{x}+{y}")

    frame = tb.Frame(win, padding=15)
    frame.pack(fill="both", expand=True)

    sections = {
        "About DupCleaner PRO": (
            "DupCleaner PRO is a professional duplicate file finder and cleaner. "
            "It allows previewing, scanning, and safely deleting duplicate files."
        ),
        "Key Features": (
            "• Drag & drop or add files/folders\n"
            "• Heuristic duplicate detection (size + hash)\n"
            "• Keep newest or first file option\n"
            "• Scrollable thumbnails preview (images)\n"
            "• Export results to TXT or JSON"
        ),
        "Usage Tips": (
            "• Add target files or folders\n"
            "• Click SCAN DUPLICATES\n"
            "• Review duplicate groups\n"
            "• Delete duplicates with caution\n"
            "• Export for record-keeping"
        ),
        "Developer": (
            "DupCleaner PRO v1.0.0\n"
            "Developed by MateTools\n"
            "https://matetools.gumroad.com"
        )
    }

    for title, text in sections.items():
        tb.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 0))
        tb.Label(frame, text=text, font=("Segoe UI", 10), wraplength=480, justify="left").pack(anchor="w", pady=(4, 8))

    tb.Button(frame, text="Close", bootstyle="danger-outline", width=15, command=win.destroy).pack(pady=15)

# =================== BUTTONS ===================
start_btn.config(command=scan_duplicates)
stop_btn.config(command=stop_scan)
delete_btn.config(command=delete_duplicates)

# =================== START ===================
app.mainloop()
