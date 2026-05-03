from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.db import init_db
from app.ui import Dashboard, LoginWindow


def build_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    bg = "#f4f7fb"
    card = "#ffffff"
    accent = "#1f4e78"
    accent2 = "#2f7ea3"
    text = "#1d2633"
    muted = "#667085"

    root.configure(bg=bg)

    style.configure("App.TFrame", background=bg)
    style.configure("Card.TFrame", background=card)
    style.configure("Header.TFrame", background=accent)
    style.configure("Title.TLabel", background=bg, foreground=text, font=("Segoe UI", 20, "bold"))
    style.configure("Subtitle.TLabel", background=bg, foreground=muted, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=card, foreground=muted, font=("Segoe UI", 9))
    style.configure("HeaderTitle.TLabel", background=accent, foreground="white", font=("Segoe UI", 18, "bold"))
    style.configure("HeaderSub.TLabel", background=accent, foreground="#dbe8f3", font=("Segoe UI", 10))
    style.configure("Section.TLabel", background=card, foreground=text, font=("Segoe UI", 13, "bold"))
    style.configure("Info.TLabel", background=card, foreground=accent2, font=("Segoe UI", 10, "bold"))
    style.configure("TButton", padding=(12, 7), font=("Segoe UI", 9))
    style.map("TButton", foreground=[("disabled", "#a0a0a0")])
    style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))


def main() -> None:
    init_db()

    root = tk.Tk()
    root.title("Client Ledger Desk")
    root.geometry("1300x820")
    root.minsize(1180, 760)
    build_style(root)

    def open_dashboard(username: str) -> None:
        for child in root.winfo_children():
            child.destroy()
        Dashboard(root, username)

    LoginWindow(root, open_dashboard)
    root.mainloop()


if __name__ == "__main__":
    main()
