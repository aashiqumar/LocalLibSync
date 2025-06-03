import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import threading
import time
import subprocess
from services.syncer import sync_output
from services.builder import build_library

CONFIG_PATH = "config/projects.json"

def load_projects():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        return data.get("libraries", [])

def save_projects(projects):
    os.makedirs("config", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"libraries": projects}, f, indent=4)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#282c34", foreground="#abb2bf", relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack()
    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def get_version(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception:
        return "?"

def add_or_edit_project(idx=None, refresh_list=None):
    # idx=None for add, otherwise edit
    if idx is not None:
        proj = projects[idx]
        title = f"Edit Library: {proj['name']}"
    else:
        proj = {
            "name": "",
            "src": "",
            "build_command": "",
            "build_output": "",
            "destinations": []
        }
        title = "Add New Library"

    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg="#23272e")
    win.geometry("540x540")
    win.resizable(False, False)

    highlight = tk.Frame(win, bg="#61afef", height=4)
    highlight.pack(fill=tk.X, side=tk.TOP)

    form = tk.Frame(win, bg="#23272e")
    form.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

    icon = tk.Label(form, text="🛠️", font=("Segoe UI", 32), bg="#23272e", fg="#61afef")
    icon.grid(row=0, column=0, columnspan=3, pady=(0, 18))

    def underline_on_focus(entry):
        underline = tk.Frame(form, height=2, bg="#282c34")
        underline.grid(row=entry.grid_info()['row']+1, column=1, columnspan=2, sticky="ew", padx=2, pady=(0, 8))
        def on_focus_in(e): underline.config(bg="#61afef")
        def on_focus_out(e): underline.config(bg="#282c34")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        return underline

    def folder_field(label, var, row, select_callback, enable_folder=True):
        tk.Label(form, text=label, bg="#23272e", fg="#abb2bf", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
        entry = ttk.Entry(form, textvariable=var, width=32)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        underline_on_focus(entry)
        if enable_folder:
            icon_btn = ttk.Button(form, text="📁", width=2, command=lambda: select_callback(force_on_top=True))
            icon_btn.grid(row=row, column=2, padx=(4, 0))
            ToolTip(icon_btn, f"Select {label.lower()}")
            def entry_select_callback(event, force_on_top=False):
                select_callback(force_on_top=True)
            entry.bind("<Button-1>", entry_select_callback)
        return entry

    name_var = tk.StringVar(value=proj['name'])
    src_var = tk.StringVar(value=proj['src'])
    out_var = tk.StringVar(value=proj['build_output'])
    build_var = tk.StringVar(value=proj['build_command'])

    # --- Folder select functions with force-on-top ---
    def select_src(force_on_top=False):
        if force_on_top:
            win.lift()
            win.attributes('-topmost', True)
        path = filedialog.askdirectory(title="Select Library Source Folder", parent=win)
        if force_on_top:
            win.attributes('-topmost', False)
        if path:
            src_var.set(path)
            if not name_var.get():
                name_var.set(os.path.basename(path))
    def select_out(force_on_top=False):
        if force_on_top:
            win.lift()
            win.attributes('-topmost', True)
        path = filedialog.askdirectory(title="Select Build Output Folder (e.g., dist/)", parent=win)
        if force_on_top:
            win.attributes('-topmost', False)
        if path:
            out_var.set(path)

    # Only the folder fields get the folder dialog, not the name
    folder_field("Library Name:", name_var, 1, lambda force_on_top=False: None, enable_folder=False)
    folder_field("Source Folder:", src_var, 2, select_src)
    folder_field("Build Output Folder:", out_var, 3, select_out)

    tk.Label(form, text="Build Command:", bg="#23272e", fg="#abb2bf", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="w", padx=(0, 10), pady=2)
    build_entry = ttk.Entry(form, textvariable=build_var, width=32)
    build_entry.grid(row=4, column=1, columnspan=2, sticky="ew", pady=2)
    underline_on_focus(build_entry)

    tk.Label(form, text="Destinations:", bg="#23272e", fg="#abb2bf", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=(10, 2))
    dest_frame = tk.Frame(form, bg="#23272e")
    dest_frame.grid(row=5, column=1, columnspan=2, sticky="ew", pady=(10, 2))
    dest_vars = [tk.StringVar(value=d) for d in proj['destinations']] or [tk.StringVar()]
    dest_entries = []

    # --- Destinations ---
    def refresh_dest_list():
        for widget in dest_frame.winfo_children():
            widget.destroy()
        for i, var in enumerate(dest_vars):
            row = tk.Frame(dest_frame, bg="#23272e")
            row.pack(fill=tk.X, pady=2)
            entry = ttk.Entry(row, textvariable=var, width=28)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            def select_dest(idx=i, force_on_top=False):
                if force_on_top:
                    win.lift()
                    win.attributes('-topmost', True)
                path = filedialog.askdirectory(title="Select Destination Folder", parent=win)
                if force_on_top:
                    win.attributes('-topmost', False)
                if path:
                    dest_vars[idx].set(path)
            icon_btn = ttk.Button(row, text="📁", width=2, command=lambda idx=i: select_dest(idx, force_on_top=True))
            icon_btn.pack(side=tk.LEFT, padx=2)
            ToolTip(icon_btn, "Select destination folder")
            entry.bind("<Button-1>", lambda e, idx=i: select_dest(idx, force_on_top=True))
            del_btn = ttk.Button(row, text="🗑", width=2, command=lambda idx=i: remove_dest(idx))
            del_btn.pack(side=tk.LEFT, padx=2)
            dest_entries.append(entry)

    def add_dest():
        dest_vars.append(tk.StringVar(value=""))
        refresh_dest_list()

    def remove_dest(idx):
        if len(dest_vars) > 1:
            dest_vars.pop(idx)
            refresh_dest_list()

    refresh_dest_list()
    add_btn = ttk.Button(dest_frame, text="➕ Add Destination", command=add_dest)
    add_btn.pack(anchor="w", pady=4)

    def on_enter(e):
        save_btn.config(style="Accent.TButton")
    def on_leave(e):
        save_btn.config(style="TButton")

    def save_edits():
        new_proj = {
            "name": name_var.get(),
            "src": src_var.get(),
            "build_output": out_var.get(),
            "build_command": build_var.get(),
            "destinations": [v.get().strip() for v in dest_vars if v.get().strip()]
        }
        if not all([new_proj["name"], new_proj["src"], new_proj["build_output"], new_proj["build_command"], new_proj["destinations"]]):
            messagebox.showwarning("Missing Data", "All fields are required and at least one destination.")
            return
        if idx is not None:
            projects[idx] = new_proj
        else:
            projects.append(new_proj)
        save_projects(projects)
        if refresh_list:
            refresh_list()
        win.destroy()

    style = ttk.Style(win)
    style.configure("Accent.TButton", background="#98c379", foreground="#23272e", font=("Segoe UI", 10, "bold"))
    save_btn = ttk.Button(form, text="💾 Save Changes" if idx is not None else "➕ Add Library", command=save_edits)
    save_btn.grid(row=99, column=0, columnspan=3, pady=18)
    save_btn.bind("<Enter>", on_enter)
    save_btn.bind("<Leave>", on_leave)

    def animate_highlight():
        # Only use 6-digit hex color, no alpha
        for i in range(0, 100, 2):
            # You can animate between two colors if you want, but keep it 6 digits
            highlight.config(bg="#61afef")
            win.update_idletasks()
            time.sleep(0.01)
        highlight.config(bg="#61afef")
        threading.Thread(target=animate_highlight, daemon=True).start()

    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(2, weight=0)



def launch_app():
    global root, projects
    root = tk.Tk()
    root.title("LocalLibSync")
    root.geometry("1100x700")
    root.configure(bg="#21252b")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#23272e")
    style.configure("TLabel", background="#23272e", foreground="#f8f8f2", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, background="#61afef", foreground="#23272e")
    style.configure("TProgressbar", thickness=12, troughcolor="#282c34", background="#61afef", bordercolor="#23272e", lightcolor="#61afef", darkcolor="#282c34")

    projects = load_projects()

    main_frame = ttk.Frame(root, padding=24, style="TFrame")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Header
    header = tk.Label(main_frame, text="📦 LocalLibSync", font=("Segoe UI", 28, "bold"), bg="#23272e", fg="#61afef")
    header.pack(pady=(0, 8))

    # Node/Angular version
    node_version = get_version("node -v")
    ng_version = get_version("ng version | grep 'Angular CLI' || true")
    tk.Label(main_frame, text=f"Node: {node_version}   |   Angular: {ng_version}", font=("Segoe UI", 10), bg="#23272e", fg="#abb2bf").pack()

    # Menu bar with Help (Instructions moved here)
    menubar = tk.Menu(root)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="How to use", command=lambda: messagebox.showinfo(
        "How to use LocalLibSync",
        (
            "Welcome to LocalLibSync!\n\n"
            "➊ Click 'Add New Project' to add a library.\n"
            "➋ For each project, set the source, build output, destination(s), and build command (e.g., ng build).\n"
            "➌ Click 'Sync' to build and sync your library to all destinations.\n"
            "➍ You can edit or remove any library.\n"
            "➎ Make sure you are using the correct Node/Angular version in your terminal (e.g., nvm use 14).\n"
        )
    ))
    helpmenu.add_command(label="About", command=lambda: messagebox.showinfo(
        "About LocalLibSync",
        "LocalLibSync helps you build and sync Angular libraries locally with ease.\n\nCreated by Rizwan Aashiq Umar.\n\nWith ♥️"
    ))
    menubar.add_cascade(label="Help", menu=helpmenu)
    root.config(menu=menubar)

    # Log output area
    log_frame = ttk.Frame(main_frame, style="TFrame")
    log_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 14))
    log_label = tk.Label(log_frame, text="Log Output", font=("Segoe UI", 10, "bold"), bg="#23272e", fg="#61afef")
    log_label.pack(anchor="w")
    log_text = tk.Text(log_frame, height=8, bg="#1e222a", fg="#98c379", font=("Consolas", 10), wrap="word", bd=2, relief="groove")
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
    log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=log_scroll.set)
    def log(msg):
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)
    ttk.Button(log_frame, text="🧹 Clear Log", command=lambda: log_text.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=5, pady=2)

    # Project area
    project_frame = ttk.Frame(main_frame, style="TFrame")
    project_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    def add_project():
        add_or_edit_project(refresh_list=refresh_list)

    def edit_project(idx):
        add_or_edit_project(idx, refresh_list=refresh_list)

    def remove_project(idx):
        if messagebox.askyesno("Remove Library", f"Are you sure you want to remove '{projects[idx]['name']}'?"):
            projects.pop(idx)
            save_projects(projects)
            refresh_list()

    def refresh_list():
        for widget in project_frame.winfo_children():
            widget.destroy()
        if not projects:
            tk.Label(project_frame, text="No projects added yet.", font=("Segoe UI", 13, "italic"), bg="#23272e", fg="#abb2bf").pack(pady=30)
            return
        for i, proj in enumerate(projects):
            card = tk.Frame(project_frame, bg="#23272e", bd=0, relief="flat", padx=0, pady=0)
            card.pack(fill=tk.X, pady=8, padx=0)

            # Animated border
            border = tk.Frame(card, bg="#61afef", height=3)
            border.pack(fill=tk.X, side=tk.TOP)

            content = tk.Frame(card, bg="#282c34", bd=2, relief="ridge", padx=10, pady=8)
            content.pack(fill=tk.X)

            # Row layout
            label = tk.Label(
                content,
                text=f"📚 {proj.get('name', 'Unnamed')}",
                font=("Segoe UI", 13, "bold"),
                bg="#282c34",
                fg="#61afef"
            )
            label.grid(row=0, column=0, sticky="w", padx=(0, 18))

            dests = "\n".join([f"→ {d}" for d in proj.get('destinations', [])])
            dest_label = tk.Label(
                content,
                text=dests,
                font=("Segoe UI", 10),
                bg="#282c34",
                fg="#abb2bf",
                justify="left"
            )
            dest_label.grid(row=0, column=1, sticky="w", padx=(0, 18))

            progress = ttk.Progressbar(content, orient="horizontal", length=120, mode="determinate")
            progress.grid(row=0, column=2, padx=(0, 18))

            sync_btn = ttk.Button(content, text="🔄", width=3, command=lambda idx=i: start_sync(idx))
            sync_btn.grid(row=0, column=3, padx=2)
            ToolTip(sync_btn, "Build and sync this library to all destinations")

            edit_btn = ttk.Button(content, text="✏️", width=3, command=lambda idx=i: edit_project(idx))
            edit_btn.grid(row=0, column=4, padx=2)
            ToolTip(edit_btn, "Edit this library")

            del_btn = ttk.Button(content, text="🗑", width=3, command=lambda idx=i: remove_project(idx))
            del_btn.grid(row=0, column=5, padx=2)
            ToolTip(del_btn, "Remove this library")

            content.grid_columnconfigure(1, weight=1)
            card.progress = progress
            card.label = label

    def start_sync(idx):
        proj = projects[idx]
        card = project_frame.winfo_children()[idx]
        progress = card.progress
        label = card.label

        def do_sync():
            try:
                # Animation: progress bar fill
                progress["value"] = 0
                label.config(text=f"🔄 {proj['name']} - Starting Sync...", fg="#e5c07b")
                for i in range(0, 101, 2):
                    progress["value"] = i
                    root.update_idletasks()
                    time.sleep(0.008)
                # Step 1: Build
                label.config(text=f"🔄 {proj['name']} - Building...", fg="#e5c07b")
                log(f"[BUILD] Building {proj['name']}...")
                success, build_output = build_library(proj)
                log(build_output)
                if not success:
                    label.config(text=f"❌ {proj['name']} - Build Failed!", fg="#e06c75")
                    log(f"[ERROR] Build failed for {proj['name']}. Sync aborted.")
                    progress["value"] = 0
                    return
                progress["value"] = 33
                root.update_idletasks()
                time.sleep(0.3)
                # Step 2: Sync to all destinations
                label.config(text=f"🔄 {proj['name']} - Syncing...", fg="#61afef")
                for dest in proj['destinations']:
                    log(f"[SYNC] Syncing {proj['name']} to {dest}...")
                    proj_copy = proj.copy()
                    proj_copy['destinations'] = [dest]
                    sync_output(proj_copy)
                progress["value"] = 66
                root.update_idletasks()
                time.sleep(0.3)
                # Step 3: Done
                label.config(text=f"✅ {proj['name']} - Sync Complete!", fg="#98c379")
                log(f"[DONE] {proj['name']} sync complete.")
                progress["value"] = 100
                root.update_idletasks()
                time.sleep(0.5)
            except Exception as e:
                log(f"[ERROR] {proj['name']}: {e}")
                label.config(text=f"❌ {proj['name']} - Error!", fg="#e06c75")
            finally:
                label.config(text=f"📚 {proj['name']}", fg="#61afef")
                progress["value"] = 0

        threading.Thread(target=do_sync, daemon=True).start()

    def simple_input(prompt):
        win = tk.Toplevel(root)
        win.title(prompt)
        win.configure(bg="#23272e")
        ttk.Label(win, text=prompt).pack(pady=5)
        entry = ttk.Entry(win, width=40)
        entry.pack(pady=5)
        value = tk.StringVar()

        def submit():
            value.set(entry.get())
            win.destroy()

        ttk.Button(win, text="OK", command=submit).pack(pady=5)
        win.wait_window()
        return value.get()

    # Main action buttons
    btn_frame = tk.Frame(main_frame, bg="#23272e")
    btn_frame.pack(fill=tk.X, pady=(0, 10))
    ttk.Button(btn_frame, text="➕ Add New Project", command=add_project).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="🔄 Reload Projects", command=refresh_list).pack(side=tk.LEFT, padx=5)

    refresh_list()
    root.mainloop()

if __name__ == "__main__":
    launch_app()