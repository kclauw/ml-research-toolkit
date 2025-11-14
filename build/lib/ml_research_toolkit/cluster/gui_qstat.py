#!/usr/bin/env python3
# qstat_gui.py - Standalone Job Table Viewer

import sys
import os
import paramiko
import json
import traceback
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import QThread, Signal

CONFIG_PATH = "~/.hpc_gui_config.json"

def load_config():
    path = os.path.expanduser(CONFIG_PATH)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

class SSHConnection:
    def __init__(self):
        self.client = None

    def connect(self, host, username, passphrase, key_path):
        key_path = os.path.expanduser(key_path)
        key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=host, username=username, pkey=key,
            look_for_keys=False, allow_agent=False
        )

    def exec(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        return out, err

class JobLoaderThread(QThread):
    jobs_loaded = Signal(list)
    error = Signal(str)
    debug = Signal(str)

    def __init__(self, ssh):
        super().__init__()
        self.ssh = ssh

    def run(self):
        try:
            out, err = self.ssh.exec("qstat")
            self.debug.emit(f"SSH output:\n{out}\nSSH error:\n{err}")
            if err:
                self.error.emit(err)
                return
            lines = (out or "").splitlines()
            if len(lines) < 3:
                self.jobs_loaded.emit([])
                return
            self.jobs_loaded.emit(lines[2:])  # skip header
        except Exception as e:
            self.error.emit(str(e))

class QstatGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HPC Job Viewer (qstat)")
        self.resize(800, 400)
        self.ssh = SSHConnection()
        self.setup_ui()
        self.auto_connect()

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

        self.job_table = QTableWidget(0, 5)
        self.job_table.setHorizontalHeaderLabels(["Job ID", "Name", "User", "State", "Raw"])
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.job_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.job_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.job_table.itemSelectionChanged.connect(
            lambda: self.kill_btn.setEnabled(bool(self.job_table.selectedItems()))
        )
        layout.addWidget(self.job_table)

    def auto_connect(self):
        cfg = load_config()
        host = cfg.get("default_host")
        user = cfg.get("default_user")
        key = cfg.get("default_key_path")
        passphrase = cfg.get("default_passphrase", "")
        if not host or not user or not key:
            QMessageBox.critical(self, "Config missing",
                                 "Please set default_host, default_user, and default_key_path in ~/.hpc_gui_config.json")
            return
        try:
            self.ssh.connect(host, user, passphrase, key)
            self.load_jobs()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Connection failed", str(e))

    def load_jobs(self):
        self.refresh_btn.setEnabled(False)
        self.loader = JobLoaderThread(self.ssh)
        self.loader.jobs_loaded.connect(self.update_table)
        self.loader.error.connect(lambda msg: QMessageBox.critical(self, "qstat error", msg))
        self.loader.debug.connect(lambda msg: print(msg))  # prints SSH output for debugging
        self.loader.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self.loader.start()

    def update_table(self, lines):
        self.job_table.blockSignals(True)
        self.job_table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            if len(line.strip()) == 0:
                continue
            # Fixed-width parsing
            jobid = line[0:10].strip()
            name  = line[10:27].strip()
            user  = line[27:44].strip()
            state = line[54:55].strip() if len(line) >= 55 else ""
            self.job_table.setItem(row, 0, QTableWidgetItem(jobid))
            self.job_table.setItem(row, 1, QTableWidgetItem(name))
            self.job_table.setItem(row, 2, QTableWidgetItem(user))
            self.job_table.setItem(row, 3, QTableWidgetItem(state))
            self.job_table.setItem(row, 4, QTableWidgetItem(line))
        self.job_table.blockSignals(False)

    def kill_selected_job(self):
        items = self.job_table.selectedItems()
        if not items:
            return
        jobid = items[0].text()
        if QMessageBox.question(self, "Kill job", f"Kill job {jobid}?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
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
