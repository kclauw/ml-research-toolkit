#!/usr/bin/env python3
# qstat_gui.py - Standalone Job Table Viewer

import sys
import paramiko
import json
import traceback
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)

CONFIG_PATH = "~/.hpc_gui_config.json"

def load_config():
    import os, json
    path = os.path.expanduser(CONFIG_PATH)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

class SSHConnection:
    def __init__(self):
        self.client = None

    def connect(self, host, username, passphrase, key_path):
        import os
        key_path = os.path.expanduser(key_path)  # <--- ADD THIS
        key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=host, username=username, pkey=key, look_for_keys=False, allow_agent=False)

    def exec(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        return out, err

class QstatGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HPC Job Viewer (qstat)")
        self.resize(800, 400)
        self.ssh = SSHConnection()
        self.setup_ui()
        self.auto_connect()
        self.load_jobs()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Jobs")
        self.refresh_btn.clicked.connect(self.load_jobs)
        self.kill_btn = QPushButton("Kill Selected Job")
        self.kill_btn.clicked.connect(self.kill_selected_job)
        self.kill_btn.setEnabled(False)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.kill_btn)
        layout.addLayout(toolbar)

        self.job_table = QTableWidget(0, 4)
        self.job_table.setHorizontalHeaderLabels(["Job ID", "User", "State", "Raw"])
        self.job_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.job_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.job_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.job_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.job_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.job_table.itemSelectionChanged.connect(lambda: self.kill_btn.setEnabled(bool(self.job_table.selectedItems())))
        layout.addWidget(self.job_table)

    def auto_connect(self):
        cfg = load_config()
        host = cfg.get("default_host")
        user = cfg.get("default_user")
        key = cfg.get("default_key_path")
        passphrase = cfg.get("default_passphrase", "")
        if not host or not user or not key:
            QMessageBox.critical(self, "Config missing", "Please set default_host, default_user, and default_key_path in ~/.hpc_gui_config.json")
            return
        try:
            self.ssh.connect(host, user, passphrase, key)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Connection failed", str(e))

    def load_jobs(self):
        try:
            out, err = self.ssh.exec("qstat -u $USER")
        except Exception as e:
            QMessageBox.critical(self, "qstat error", str(e))
            return
        lines = (out or "").splitlines()
        self.job_table.setRowCount(0)
        if len(lines) < 3:
            return
        for line in lines[2:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            jobid, user, state = parts[0], parts[1], parts[4]
            row = self.job_table.rowCount()
            self.job_table.insertRow(row)
            self.job_table.setItem(row, 0, QTableWidgetItem(jobid))
            self.job_table.setItem(row, 1, QTableWidgetItem(user))
            self.job_table.setItem(row, 2, QTableWidgetItem(state))
            self.job_table.setItem(row, 3, QTableWidgetItem(line))

    def kill_selected_job(self):
        items = self.job_table.selectedItems()
        if not items:
            return
        jobid = items[0].text()
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Kill job", f"Kill job {jobid}?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            out, err = self.ssh.exec(f"qdel {jobid}")
            QMessageBox.information(self, "Kill", out or err or "Command sent")
            self.load_jobs()
        except Exception as e:
            QMessageBox.critical(self, "Kill error", str(e))

def main():
    app = QApplication(sys.argv)
    gui = QstatGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
