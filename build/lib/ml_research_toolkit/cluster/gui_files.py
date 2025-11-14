#!/usr/bin/env python3
# run_gui.py - Updated with navigation & download

import sys
import os
import stat
import traceback
import paramiko
import keyring
import json
import re
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QSplitter, QDialog, QAbstractItemView
)
from PySide6.QtCore import Qt

# ---------- Config utils ----------
CONFIG_PATH = os.path.expanduser("~/.hpc_gui_config.json")

def load_local_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_local_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Failed to save config:", e)

# ---------- SSH / SFTP wrapper ----------
class SSHConnection:
    def __init__(self):
        self.client = None
        self.sftp = None
        self.host = None
        self.username = None
        self.port = 22

    def connect(self, host, username, passphrase, port=22, key_path=None, password=None, allow_agent=True):
        self.close()
        key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(key_path), password=passphrase)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                hostname=host,
                username=username,
                pkey=key,
                look_for_keys=False,
                allow_agent=False,
                timeout=15
            )
            print("SUCCESS: SSH login worked!")
        except Exception as e:
            print("ERROR:", e)
            raise e

        self.sftp = self.client.open_sftp()

    def exec(self, cmd, timeout=30):
        if not self.client:
            raise RuntimeError("Not connected")
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors='ignore')
        err = stderr.read().decode(errors='ignore')
        return out, err

    def listdir_attr(self, path):
        if not self.sftp:
            raise RuntimeError("SFTP not initialized")
        return self.sftp.listdir_attr(path)

    def stat(self, path):
        return self.sftp.stat(path)

    def isdir(self, path):
        try:
            mode = self.sftp.stat(path).st_mode
            return stat.S_ISDIR(mode)
        except IOError:
            return False

    def remove(self, path):
        return self.sftp.remove(path)

    def rmdir(self, path):
        return self.sftp.rmdir(path)

    def close(self):
        try:
            if self.sftp:
                self.sftp.close()
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        self.sftp = None
        self.client = None

# ---------- GUI ----------
class HPCGui(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_local_config()
        self.setWindowTitle("HPC File Browser")
        self.resize(1100, 700)
        self.ssh = SSHConnection()
        self.current_path = self.config.get("default_start_dir", "/data/gent/433/vsc43397")
        self._open_dialogs = []

        # Base folders for download
        self.cluster_folder = "/data/gent/433/vsc43397/ibac-original/ib_actor_critic/runs/"
        self.local_folder = "/Users/kenzoclauw/Research/ibac-original/ib_actor_critic/runs/"

        self.setup_ui()
        self.auto_connect()

    # ---------- UI setup ----------
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Top bar
        dir_layout = QHBoxLayout()
        self.cwd_label = QLabel(f"Current: {self.current_path}")
        self.up_btn = QPushButton("Up")
        self.up_btn.clicked.connect(self.on_tree_up)
        self.refresh_files_btn = QPushButton("Refresh")
        self.refresh_files_btn.clicked.connect(self.refresh_file_list)
        self.delete_file_btn = QPushButton("Delete selected")
        self.delete_file_btn.clicked.connect(self.delete_selected_file)
        self.view_file_btn = QPushButton("View file content")
        self.view_file_btn.clicked.connect(self.view_selected_file)
        self.download_btn = QPushButton("Download selected")
        self.download_btn.clicked.connect(self.download_selected)

        dir_layout.addWidget(self.cwd_label)
        dir_layout.addWidget(self.up_btn)
        dir_layout.addWidget(self.refresh_files_btn)
        dir_layout.addWidget(self.delete_file_btn)
        dir_layout.addWidget(self.view_file_btn)
        dir_layout.addWidget(self.download_btn)
        layout.addLayout(dir_layout)

        # File table
        self.file_table = QTableWidget(0, 4)
        self.file_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_table.itemDoubleClicked.connect(self.on_file_doubleclick)
        layout.addWidget(self.file_table)

        # Raw output log
        self.raw_output = QTextEdit()
        self.raw_output.setReadOnly(True)
        layout.addWidget(self.raw_output)

    # ---------- Auto-connect ----------
    def auto_connect(self):
        host = self.config.get("default_host")
        user = self.config.get("default_user")
        key = self.config.get("default_key_path")
        passphrase = self.config.get("default_passphrase", "")
        if not host or not user or not key:
            QMessageBox.critical(self, "Config missing",
                                 "Please set default_host, default_user, and default_key_path in ~/.hpc_gui_config.json")
            return
        try:
            self.ssh.connect(host=host, username=user, passphrase=passphrase, key_path=key)
            self.raw_output.append(f"Connected to {host} as {user}")
            self.refresh_file_list()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Connection failed", str(e))

    # ---------- File operations ----------
    def refresh_file_list(self):
        path = self.current_path
        self.file_table.setRowCount(0)
        self.cwd_label.setText(f"Current: {path}")
        self.raw_output.append(f"Listing: {path}")
        try:
            attrs = self.ssh.listdir_attr(path)
        except Exception as e:
            QMessageBox.critical(self, "List error", f"Could not list {path}: {e}")
            return

        entries = []
        for a in attrs:
            name = a.filename
            if name in (".", ".."): continue
            full = path.rstrip("/") + "/" + name if path != "/" else "/" + name
            is_dir = stat.S_ISDIR(a.st_mode)
            entries.append((name, full, is_dir, a.st_size, a.st_mtime))
        entries.sort(key=lambda x: (not x[2], x[0].lower()))

        for name, full, is_dir, size, mtime in entries:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            item_name = QTableWidgetItem(name + ("/" if is_dir else ""))
            item_type = QTableWidgetItem("Directory" if is_dir else "File")
            item_size = QTableWidgetItem("" if is_dir else str(size))
            item_mtime = QTableWidgetItem(str(mtime))
            item_name.setData(Qt.UserRole, full)
            self.file_table.setItem(row, 0, item_name)
            self.file_table.setItem(row, 1, item_type)
            self.file_table.setItem(row, 2, item_size)
            self.file_table.setItem(row, 3, item_mtime)

    def on_tree_up(self):
        if self.current_path == "/": return
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if parent == "": parent = "/"
        self.current_path = parent
        self.refresh_file_list()

    def delete_selected_file(self):
        sel = self.file_table.selectedItems()
        if not sel: return
        rows = set(item.row() for item in sel)
        paths = [self.file_table.item(row, 0).data(Qt.UserRole) for row in rows]
        if QMessageBox.question(self, "Delete", f"Delete {len(paths)} files/folders?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        for path in paths:
            try:
                if self.ssh.isdir(path):
                    self.ssh.rmdir(path)
                else:
                    self.ssh.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Delete failed", str(e))
        self.refresh_file_list()

    def view_selected_file(self):
        selected = self.file_table.selectedItems()
        if not selected: return
        row = selected[0].row()
        path = self.file_table.item(row, 0).data(Qt.UserRole)
        if self.ssh.isdir(path):
            QMessageBox.information(self, "Folder", "Cannot display folder content")
            return

        if not re.search(r"\.(e|o)\d+$", path) and not path.endswith((".txt", ".log")):
            QMessageBox.information(self, "Unsupported file", "Can only display .e*, .o*, .txt, .log files")
            return

        try:
            with self.ssh.sftp.file(path, "r") as f:
                content = f.read().decode(errors="ignore")

            dlg = QDialog(self)
            dlg.setWindowTitle(f"Content: {os.path.basename(path)}")
            dlg.resize(800, 600)
            layout = QVBoxLayout(dlg)
            text_area = QTextEdit()
            text_area.setReadOnly(True)
            text_area.setPlainText(content)
            layout.addWidget(text_area)
            dlg.show()
            self._open_dialogs.append(dlg)

        except Exception as e:
            QMessageBox.critical(self, "Error reading file", str(e))

    # ---------- Download / Navigation ----------
    def on_file_doubleclick(self, item):
        row = item.row()
        path = self.file_table.item(row, 0).data(Qt.UserRole)
        if self.ssh.isdir(path):
            self.current_path = path
            self.refresh_file_list()
        else:
            self.download_file_or_folder(path)

    def download_file_or_folder(self, remote_path):
        rel_path = os.path.relpath(remote_path, self.cluster_folder)
        local_path = os.path.join(self.local_folder, rel_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if self.ssh.isdir(remote_path):
            for attr in self.ssh.listdir_attr(remote_path):
                name = attr.filename
                if name in (".", ".."): continue
                self.download_file_or_folder(os.path.join(remote_path, name))
        else:
            try:
                self.raw_output.append(f"Downloading: {remote_path} -> {local_path}")
                self.ssh.sftp.get(remote_path, local_path)
            except Exception as e:
                QMessageBox.critical(self, "Download failed", str(e))

    def download_selected(self):
        sel = self.file_table.selectedItems()
        if not sel: return
        rows = set(item.row() for item in sel)
        paths = [self.file_table.item(row, 0).data(Qt.UserRole) for row in rows]
        for path in paths:
            self.download_file_or_folder(path)

# ---------- Main ----------
def main():
    app = QApplication(sys.argv)
    gui = HPCGui()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

