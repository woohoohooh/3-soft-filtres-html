import os
import shutil
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import List
import keyboard

@dataclass
class FolderItem:
    path: str
    number: int
    display_name: str

class HTMLManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка HTML")
        self.root.geometry("900x600")

        self.root.configure(bg='#1a1a1a')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1a1a1a', foreground='#e0e0e0')
        style.configure('TFrame', background='#1a1a1a')
        style.configure('TButton', background='#2d2d2d', foreground='#e0e0e0', bordercolor='#404040')
        style.map('TButton', background=[('active', '#3d3d3d')])
        style.configure('TEntry', fieldbackground='#2d2d2d', foreground='#e0e0e0', insertcolor='#e0e0e0')
        style.configure('TCombobox', fieldbackground='#2d2d2d', foreground='#e0e0e0', background='#2d2d2d')

        self.current_dir = os.getcwd()
        self.folders = []
        self.html_files = []
        self.selected_index = 0
        self.processed_files = set()
        self.alt_tab_scheduled = False
        self.mouse_clicked = False

        self.load_folders()
        self.setup_ui()
        self.refresh_html_list()
        self.update_title_stats()

        self.root.bind('<Up>', self.move_up)
        self.root.bind('<Down>', self.move_down)
        self.root.bind('<Return>', self.open_selected)
        self.root.bind('<Key>', self.on_key_press)
        for i in range(10):
            self.root.bind(str(i), lambda e, num=i: self.copy_to_folder(num if num != 0 else 10))

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key == 'e' or key == 'у' or key == 'E' or key == 'У':
            self.move_down(event)
        elif key == 'q' or key == 'й' or key == 'Q' or key == 'Й':
            self.move_up(event)

    def load_folders(self):
        self.folders = []
        items = os.listdir(self.current_dir)
        folder_paths = [os.path.join(self.current_dir, item) for item in items
                        if os.path.isdir(os.path.join(self.current_dir, item)) and not item.endswith('-checked')]

        for i, folder_path in enumerate(folder_paths[:10], 1):
            display_name = os.path.basename(folder_path)
            self.folders.append(FolderItem(folder_path, i, display_name))

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))

        folders_container = ttk.Frame(top_frame)
        folders_container.pack(fill=tk.X)

        self.folders_frame = ttk.Frame(folders_container)
        self.folders_frame.pack(fill=tk.X)

        new_folder_frame = ttk.Frame(folders_container)
        new_folder_frame.pack(fill=tk.X, pady=(2, 0))

        self.new_folder_var = tk.StringVar()
        self.new_folder_entry = ttk.Entry(new_folder_frame, textvariable=self.new_folder_var, width=30)
        self.new_folder_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.new_folder_entry.bind('<Return>', self.create_folder)

        self.number_var = tk.StringVar()
        self.number_combo = ttk.Combobox(new_folder_frame, textvariable=self.number_var, width=5, state='readonly')
        self.number_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.update_number_combo()

        self.create_btn = ttk.Button(new_folder_frame, text="📁", width=3, command=self.create_folder)
        self.create_btn.pack(side=tk.LEFT, padx=(0, 2))

        self.cleanup_btn = ttk.Button(new_folder_frame, text="🗑️", width=3, command=self.cleanup_files)
        self.cleanup_btn.pack(side=tk.LEFT)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.html_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 11),
            activestyle='none',
            bg='#2d2d2d',
            fg='#e0e0e0',
            selectbackground='#3a4c6b',
            selectforeground='#ffffff',
            selectmode=tk.SINGLE,
            bd=0,
            highlightthickness=0
        )
        self.html_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.html_listbox.yview)

        self.html_listbox.bind('<Button-1>', self.on_listbox_click)
        self.html_listbox.bind('<<ListboxSelect>>', self.on_select)
        self.html_listbox.bind('<Double-Button-1>', self.open_selected)

        self.update_folders_display()

    def update_number_combo(self):
        used = {f.number for f in self.folders}
        available = [str(i) for i in range(10) if i not in used]
        self.number_combo['values'] = available
        self.number_combo.set('')

    def on_listbox_click(self, event):
        index = self.html_listbox.nearest(event.y)
        if 0 <= index < len(self.html_files):
            self.selected_index = index
            self.update_selection()
            self.open_current_in_browser()

    def update_folders_display(self):
        for widget in self.folders_frame.winfo_children():
            widget.destroy()

        self.folders.sort(key=lambda x: x.number)

        for folder in self.folders:
            if folder.number > 10:
                continue

            frame = ttk.Frame(self.folders_frame)
            frame.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

            btn_text = f"{folder.number}. {folder.display_name}"
            btn = ttk.Button(frame, text=btn_text, command=lambda f=folder: self.open_folder(f))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.update_number_combo()

    def update_title_stats(self):
        total = len(self.html_files)
        processed = len([f for f in self.html_files if f in self.processed_files])
        self.root.title(f"Обработано: {processed}/{total}")

    def refresh_html_list(self):
        self.html_files = []
        items = os.listdir(self.current_dir)
        for item in items:
            if item.lower().endswith('.html') and os.path.isfile(os.path.join(self.current_dir, item)):
                self.html_files.append(item)

        self.html_files.sort()

        current_selection = self.selected_index
        self.html_listbox.delete(0, tk.END)

        for i, file in enumerate(self.html_files):
            folders_for_file = []
            for folder in self.folders:
                folder_path = os.path.join(folder.path, file)
                if os.path.exists(folder_path):
                    folders_for_file.append(folder.display_name)

            display_text = file
            if folders_for_file:
                display_text = f"{file} — {', '.join(folders_for_file)}"
            elif file in self.processed_files:
                display_text = f"✓ {file}"

            self.html_listbox.insert(tk.END, display_text)

        if self.html_files:
            if current_selection < len(self.html_files):
                self.selected_index = current_selection
            else:
                self.selected_index = len(self.html_files) - 1
            self.update_selection()
        else:
            self.selected_index = -1

        self.update_title_stats()

    def update_selection(self):
        if self.selected_index >= 0 and self.html_files:
            self.html_listbox.selection_clear(0, tk.END)
            self.html_listbox.selection_set(self.selected_index)
            self.html_listbox.activate(self.selected_index)
            self.html_listbox.see(self.selected_index)

    def on_select(self, event):
        selection = self.html_listbox.curselection()
        if selection and not self.mouse_clicked:
            self.selected_index = selection[0]

    def move_up(self, event):
        if self.selected_index > 0:
            self.selected_index -= 1
            self.update_selection()
            self.open_current_in_browser()

    def move_down(self, event):
        if self.selected_index < len(self.html_files) - 1:
            self.selected_index += 1
            self.update_selection()
            self.open_current_in_browser()

    def open_current_in_browser(self):
        if 0 <= self.selected_index < len(self.html_files):
            file_path = os.path.join(self.current_dir, self.html_files[self.selected_index])
            webbrowser.open(f'file://{file_path}')

            if not self.alt_tab_scheduled:
                self.alt_tab_scheduled = True
                threading.Timer(0.3, self.do_alt_tab).start()

    def open_selected(self, event=None):
        self.open_current_in_browser()

    def do_alt_tab(self):
        try:
            keyboard.press_and_release('alt+tab')
        except:
            pass
        finally:
            self.alt_tab_scheduled = False

    def copy_to_folder(self, number):
        if not (1 <= number <= 10) or self.selected_index < 0 or self.selected_index >= len(self.html_files):
            return

        folder = next((f for f in self.folders if f.number == number), None)
        if not folder:
            return

        file_name = self.html_files[self.selected_index]
        src = os.path.join(self.current_dir, file_name)
        dst = os.path.join(folder.path, file_name)

        try:
            shutil.copy2(src, dst)
            self.processed_files.add(file_name)

            if self.selected_index < len(self.html_files) - 1:
                next_index = self.selected_index + 1
            else:
                next_index = self.selected_index

            self.refresh_html_list()
            self.selected_index = next_index
            self.update_selection()
            self.open_current_in_browser()

        except Exception as e:
            print(f"Error copying: {e}")

    def open_folder(self, folder):
        try:
            os.startfile(folder.path)
        except:
            pass

    def create_folder(self, event=None):
        folder_name = self.new_folder_var.get().strip()
        number_str = self.number_var.get().strip()

        if not folder_name or not number_str:
            return

        try:
            number = int(number_str)
        except ValueError:
            return

        if number in {f.number for f in self.folders}:
            return

        folder_path = os.path.join(self.current_dir, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.folders.append(FolderItem(folder_path, number, folder_name))
            self.folders.sort(key=lambda x: x.number)

            current_selection = self.selected_index
            self.update_folders_display()
            self.refresh_html_list()
            self.selected_index = current_selection
            self.update_selection()

            self.new_folder_var.set("")
            self.number_var.set("")
            self.update_number_combo()

        except Exception as e:
            print(f"Error creating folder: {e}")

    def cleanup_files(self):
        checked_dir = os.path.join(self.current_dir, "-checked")
        os.makedirs(checked_dir, exist_ok=True)

        for file_name in self.html_files:
            src = os.path.join(self.current_dir, file_name)
            dst = os.path.join(checked_dir, file_name)
            try:
                shutil.move(src, dst)
            except:
                pass

        self.processed_files.clear()
        self.refresh_html_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = HTMLManagerApp(root)
    root.mainloop()