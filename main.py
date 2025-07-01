import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from ppadb.client import Client as AdbClient
import os
import threading

class AdbFileExplorer(tk.Tk):
    """
    A simple file explorer for an Android device using ADB and Tkinter.
    """
    def __init__(self):
        super().__init__()
        self.title("Android ADB File Explorer")
        self.geometry("800x600")

        self.client = None
        self.device = None
        self.current_path = "/"
        self.is_path_link_stack = [False]

        self.create_widgets()
        self.connect_to_device()

    def create_widgets(self):
        """
        Creates the UI elements for the file explorer.
        """
        # Frame for the path and up button
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        self.path_label = tk.Label(top_frame, text=self.current_path, anchor="w")
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.up_button = tk.Button(top_frame, text="Up", command=self.go_up)
        self.up_button.pack(side=tk.RIGHT)

        # Sorting option
        self.sort_var = tk.StringVar(value="Name")
        self.sort_menu = tk.OptionMenu(top_frame, self.sort_var, "Name", "Created Time", command=lambda _: self.refresh_list())
        self.sort_menu.pack(side=tk.RIGHT, padx=5)

        # Sorting direction option
        self.sort_dir_var = tk.StringVar(value="Descending")
        self.sort_dir_menu = tk.OptionMenu(top_frame, self.sort_dir_var, "Ascending", "Descending", command=lambda _: self.refresh_list())
        self.sort_dir_menu.pack(side=tk.RIGHT, padx=5)

        # Listbox to display files and folders
        self.file_list = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.file_list.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.file_list.bind("<Double-1>", self.on_item_double_click)

        # Frame for the action buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self.export_button = tk.Button(bottom_frame, text="Export File", command=self.export_file)
        self.export_button.pack(side=tk.LEFT)

        self.refresh_button = tk.Button(bottom_frame, text="Refresh", command=self.refresh_list)
        self.refresh_button.pack(side=tk.RIGHT)


    def connect_to_device(self):
        """
        Connects to the first available ADB device.
        """
        try:
            self.client = AdbClient(host="127.0.0.1", port=5037)
            devices = self.client.devices()
            if len(devices) == 0:
                messagebox.showerror("Error", "No device connected. Please ensure your device is connected and in debug mode.")
                self.destroy()
                return
            self.device = devices[0]
            self.list_files(self.current_path)
        except Exception as e:
            # This can happen if the adb server isn't running.
            messagebox.showerror("Error", f"Failed to connect to ADB: {e}\n\nPlease ensure the ADB server is running.")
            self.destroy()

    def list_files(self, path):
        """
        Lists the files and folders in the given path on the device.
        """
        self.current_path = path
        self.path_label.config(text=self.current_path)
        self.file_list.delete(0, tk.END)
        try:
            sort_by = self.sort_var.get() if hasattr(self, 'sort_var') else "Name"
            sort_dir = self.sort_dir_var.get() if hasattr(self, 'sort_dir_var') else "Ascending"
            reverse = sort_dir == "Descending"
            print(self.is_path_link_stack)
            if self.is_path_link_stack[-1]:
                result = self.device.shell(f"ls -la {path+'/'}")
            else:
                result = self.device.shell(f"ls -la '{path}'")
            lines = result.splitlines()
            files = []
            for line in lines:
                # Skip total line
                if line.strip().startswith('total'):
                    continue
                parts = line.split()
                if len(parts) < 8:
                    continue
                if parts[4] == "?":
                    continue
                name = parts[7]
                if name in ['.', '..']:
                    continue
                time_str = ' '.join(parts[5:7])
                perm = parts[0]
                file_type = 'other'
                if perm.startswith('d'):
                    file_type = 'dir'
                elif perm.startswith('-'):
                    file_type = 'file'
                elif perm.startswith('l'):
                    # Symlink: need to check if it points to a dir or file
                    # Example: lrwxrwxrwx 1 user group 11 date time symlink -> /path/to/target
                    if '->' in line:
                        target = line.split('->', 1)[1].strip().split(' ')[0]
                        # Query the target type
                        target_path = target
                        if not target_path.startswith('/'):
                            target_path = os.path.join(path, target_path).replace('\\', '/')
                        try:
                            target_stats = self.device.shell(f"ls -ld '{target_path}'")
                            target_stats = self.examine_path_stats(target_stats, target_path)
                            if target_stats.startswith('d'):
                                file_type = 'symlink_dir'
                            else:
                                file_type = 'symlink_file'
                        except Exception:
                            file_type = 'symlink_file'  # fallback
                    else:
                        file_type = 'symlink_file'  # fallback
                files.append({'name': name, 'time': time_str, 'raw': line, 'file_type': file_type})
            if sort_by == "Name":
                files.sort(key=lambda x: x['name'].lower(), reverse=reverse)
            elif sort_by == "Created Time":
                from datetime import datetime
                def parse_time(file):
                    try:
                        return datetime.strptime(file['time'], "%Y-%m-%d %H:%M")
                    except Exception:
                        try:
                            return datetime.strptime(file['time'], "%b %d %H:%M")
                        except Exception:
                            return file['time']
                files.sort(key=parse_time, reverse=reverse)
            for file in files:
                display_name = self.get_display_name(file['name'], file['file_type'])
                self.file_list.insert(tk.END, display_name)
        except Exception as e:
            messagebox.showerror("Error", f"Could not list files in {self.current_path}: {e}")
            # If we can't list the directory, go back up to the parent.
            self.go_up()

    def get_display_name(self, name, file_type):
        """
        Returns the display name with icon for a file, folder, or symlink.
        file_type: 'dir', 'file', 'symlink_dir', 'symlink_file', or 'other'
        """
        if file_type == 'dir':
            icon = "📁"
        elif file_type == 'file':
            icon = "📄"
        elif file_type == 'symlink_dir':
            icon = "🔗📁"
        elif file_type == 'symlink_file':
            icon = "🔗📄"
        else:
            icon = "❓"
        return f"{icon} {name}"

    def get_real_name_from_display(self, display_name):
        """
        Extracts the real file/folder name from the display name with icon.
        """
        return display_name.split(' ', 1)[1] if ' ' in display_name else display_name

    def examine_path_stats(self, stats, new_path):
        max_symlink_depth = 10
        current_path = new_path
        depth = 0
        while stats.startswith('l') and depth < max_symlink_depth:
            if '->' in stats:
                parts = stats.split('->')
                if len(parts) > 1:
                    target_path = parts[1].strip().split(' ')[0]
                    if not target_path.startswith('/'):
                        parent_dir = os.path.dirname(current_path)
                        target_path = os.path.join(parent_dir, target_path).replace('\\', '/')
                    current_path = target_path
                    stats = self.device.shell(f"ls -ld '{current_path}'")
                    depth += 1
                else:
                    break  # Malformed symlink
            else:
                break  # Symlink without target
        return stats

    def on_item_double_click(self, event):
        """
        Handles double-click events on the file list.
        Navigates into directories.
        """
        selection = self.file_list.curselection()
        if not selection:
            return
        
        selected_item = self.file_list.get(selection[0])
        # Use os.path.join and then replace backslashes for cross-platform compatibility
        new_path = os.path.join(self.current_path, self.get_real_name_from_display(selected_item)).replace("\\", "/")
        
        # To check if an item is a directory, we check the output of 'ls -ld'.
        # The output for a directory will start with the letter 'd'.
        try:
            # Using single quotes around the path handles spaces and special characters
            stats = self.device.shell(f"ls -ld '{new_path}'")
            if stats.startswith('l'):
                self.is_path_link_stack.append(True)
                stats = self.examine_path_stats(stats, new_path)
            elif stats.startswith('d'):
                self.is_path_link_stack.append(False)
            if stats.startswith('d'):
                self.list_files(new_path)
            # else: do nothing for files or unresolved/malformed links
        except Exception as e:
            # This can happen for items like broken symbolic links.
            messagebox.showwarning("Info", f"Could not determine item type for {selected_item}.\nError: {e}")

    def go_up(self):
        """
        Navigates to the parent directory.
        """
        # Use os.path.dirname and then replace backslashes for cross-platform compatibility
        print(os.path.dirname(self.current_path))
        new_path = os.path.dirname(self.current_path).replace("\\", "/")
        print(f"Going up from {self.current_path} to {new_path}")
        if new_path != self.current_path:
            self.is_path_link_stack.pop()
            self.list_files(new_path)

    def export_file(self):
        """
        Exports the selected file(s) from the device to the local machine.
        """
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select file(s) to export.")
            return

        # Ask for a directory to save all selected files
        local_dir = filedialog.askdirectory(title="Select directory to save files")
        if not local_dir:
            return

        failed = []
        for idx in selection:
            filename = self.file_list.get(idx)
            real_name = self.get_real_name_from_display(filename)
            remote_path = os.path.join(self.current_path, real_name).replace("\\", "/")
            local_path = os.path.join(local_dir, real_name)
            try:
                self.device.pull(remote_path, local_path)
            except Exception as e:
                failed.append(real_name)
        if failed:
            messagebox.showerror("Error", f"Failed to export: {', '.join(failed)}")
        else:
            messagebox.showinfo("Success", f"All selected files exported to {local_dir}")

    def refresh_list(self):
        """
        Refreshes the file list in the current directory.
        """
        self.list_files(self.current_path)


if __name__ == "__main__":
    # Before running, make sure you have the correct adb library installed:
    # pip install pure-python-adb
    app = AdbFileExplorer()
    app.mainloop()

