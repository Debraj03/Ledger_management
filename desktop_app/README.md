# Client Ledger Desk

Tkinter desktop app for client management, bulk ledger entry, and Excel export.

Run:

```bash
pip install -r requirements.txt
python main.py
```

Build a downloadable Windows executable:

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --name ClientLedgerDesk --icon assets/app_logo.jpg main.py
```

The packaged `.exe` will be created under `dist/`.
