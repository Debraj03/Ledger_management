from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import importlib
from typing import Callable
from datetime import datetime

from . import repository as repo


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, height=190)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)

        self.inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class LoginWindow(ttk.Frame):
    def __init__(self, master: tk.Tk, on_success: Callable[[str], None], logo_image: tk.PhotoImage | None = None):
        super().__init__(master, padding=24)
        self.master = master
        self.on_success = on_success
        self.logo_image = logo_image

        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        if self.logo_image is not None:
            ttk.Label(header, image=self.logo_image).pack(anchor="w", pady=(0, 8))
        ttk.Label(header, text="Client Ledger Desk", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Two-screen workflow: Ledger Management and Client Management.",
            style="Subtitle.TLabel",
            wraplength=560,
        ).pack(anchor="w", pady=(6, 0))

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Username").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.username = ttk.Entry(card, width=30)
        self.username.grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(card, text="Password").grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.password = ttk.Entry(card, show="*", width=30)
        self.password.grid(row=1, column=1, sticky="ew", pady=(0, 8))

        buttons = ttk.Frame(card)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="Login", command=self.login).pack(side="left")
        ttk.Button(buttons, text="Register", command=self.register).pack(side="left", padx=10)

        ttk.Label(card, text="Use Register the first time, then Login.", style="Muted.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(14, 0)
        )

        self.pack(fill="both", expand=True)
        self.username.focus_set()

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            messagebox.showwarning("Missing data", "Enter both username and password.")
            return
        if not repo.authenticate_user(username, password):
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        self.destroy()
        self.on_success(username)

    def register(self):
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            messagebox.showwarning("Missing data", "Enter both username and password.")
            return
        try:
            repo.create_user(username, password)
        except Exception as exc:
            messagebox.showerror("Registration failed", f"Could not register user:\n{exc}")
            return
        messagebox.showinfo("Success", "User registered. You can log in now.")


class LedgerEntryModal(tk.Toplevel):
    def __init__(self, parent: "Dashboard"):
        super().__init__(parent.master)
        self.parent = parent
        self.rows: list[dict[str, ttk.Entry | ttk.Frame]] = []

        self.title("Add Ledger Entries")
        self.geometry("680x480")
        self.resizable(True, True)
        self.transient(parent.master)
        self.grab_set()

        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Add Ledger", style="Section.TLabel").pack(anchor="w")

        top = ttk.Frame(container)
        top.pack(fill="x", pady=(8, 8))
        ttk.Label(top, text="Client").pack(side="left")

        self.client_choice = tk.StringVar()
        self.client_combo = ttk.Combobox(top, textvariable=self.client_choice, state="readonly", width=42)
        self.client_combo.pack(side="left", padx=8)

        for value in self.parent.get_client_combo_values():
            pass
        self.client_combo["values"] = self.parent.get_client_combo_values()

        if self.parent.current_client_id:
            client = repo.get_client(self.parent.current_client_id)
            if client:
                self.client_choice.set(f"{client['id']} - {client['name']}")
        elif self.client_combo["values"]:
            self.client_choice.set(self.client_combo["values"][0])

        ttk.Button(top, text="Add Row", command=self.add_row).pack(side="left", padx=(8, 0))

        self.rows_holder = ScrollableFrame(container)
        self.rows_holder.pack(fill="both", expand=True, pady=(6, 8))

        footer = ttk.Frame(container)
        footer.pack(fill="x")
        ttk.Button(footer, text="Save Entries", command=self.save_entries).pack(side="left")
        ttk.Button(footer, text="Close", command=self.destroy).pack(side="right")

        self.add_row()
        self.add_row()

    def add_row(self):
        row_frame = ttk.Frame(self.rows_holder.inner)
        row_frame.pack(fill="x", pady=4)
        
        product_name = ttk.Entry(row_frame, width=16)
        product_name.insert(0, "")
        ttk.Label(row_frame, text="Product").pack(side="left")
        product_name.pack(side="left", padx=(8, 16))
        
        qty = ttk.Entry(row_frame, width=12)
        price = ttk.Entry(row_frame, width=12)
        qty.insert(0, "0")
        price.insert(0, "0")
        ttk.Label(row_frame, text="Qty (kg)").pack(side="left")
        qty.pack(side="left", padx=(8, 12))
        ttk.Label(row_frame, text="Price/kg").pack(side="left")
        price.pack(side="left", padx=(8, 16))
        
        # Date picker button
        self.selected_date = tk.StringVar(value=datetime.now(repo.IST).strftime("%Y-%m-%d"))
        date_label = ttk.Label(row_frame, text="Date: " + self.selected_date.get())
        date_label.pack(side="left", padx=(8, 4))

        def open_calendar():
            try:
                tkcalendar = importlib.import_module("tkcalendar")
            except ImportError:
                messagebox.showerror("Missing dependency", "Install tkcalendar to use the date picker.")
                return

            cal_window = tk.Toplevel(row_frame)
            cal_window.title("Select Date")
            cal = tkcalendar.DateEntry(
                cal_window,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=2,
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day,
            )
            cal.pack(padx=10, pady=10)

            def select_date():
                selected = cal.get_date()
                self.selected_date.set(str(selected))
                date_label.config(text="Date: " + str(selected))
                row_data["selected_date"] = self.selected_date.get()
                cal_window.destroy()

            ttk.Button(cal_window, text="OK", command=select_date).pack(padx=10, pady=5)
        
        ttk.Button(row_frame, text="📅", command=open_calendar).pack(side="left", padx=(4, 16))
        
        ttk.Button(row_frame, text="Remove", command=lambda: self.remove_row(row_frame)).pack(side="left")
        
        row_data = {"frame": row_frame, "product_name": product_name, "qty": qty, "price": price, "selected_date": self.selected_date.get()}
        self.rows.append(row_data)

    def remove_row(self, frame: ttk.Frame):
        self.rows = [row for row in self.rows if row["frame"] != frame]
        frame.destroy()

    def selected_client_id(self) -> int | None:
        value = self.client_choice.get().strip()
        if not value:
            return None
        try:
            return int(value.split(" - ", 1)[0])
        except ValueError:
            return None

    def save_entries(self):
        client_id = self.selected_client_id()
        if not client_id:
            messagebox.showwarning("Missing client", "Select a client.")
            return

        entries = []
        for row in self.rows:
            try:
                product_name = row["product_name"].get().strip()
                qty = float(row["qty"].get().strip())
                price = float(row["price"].get().strip())
                created_at = row.get("selected_date", datetime.now(repo.IST).strftime("%Y-%m-%d"))
            except ValueError:
                messagebox.showerror("Invalid data", "Quantity and price must be numeric.")
                return
            if qty <= 0 or price <= 0:
                messagebox.showerror("Invalid data", "Quantity and price must be greater than zero.")
                return
            if not product_name:
                messagebox.showerror("Invalid data", "Product name cannot be empty.")
                return
            entries.append({
                "product_name": product_name,
                "quantity_kg": qty,
                "price_per_kg": price,
                "created_at": created_at + "T00:00:00"  # Convert date to ISO format
            })

        if not entries:
            messagebox.showwarning("No data", "Add at least one row.")
            return

        try:
            repo.create_ledgers(client_id, entries)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.parent.current_client_id = client_id
        self.parent.sync_client_filter()
        self.parent.refresh_all()
        messagebox.showinfo("Saved", "Ledger entries added successfully.")
        self.destroy()


class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent: "Dashboard"):
        super().__init__(parent.master)
        self.parent = parent
        self.title("Change User Password")
        self.geometry("420x200")
        self.transient(parent.master)
        self.grab_set()

        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Select User", style="Section.TLabel").pack(anchor="w")
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(container, textvariable=self.user_var, state="readonly")
        self.user_combo.pack(fill="x", pady=(6, 8))
        self.user_combo["values"] = repo.list_users()

        ttk.Label(container, text="New Password").pack(anchor="w")
        self.pw = ttk.Entry(container, show="*")
        self.pw.pack(fill="x", pady=(0, 8))

        ttk.Label(container, text="Confirm Password").pack(anchor="w")
        self.pw2 = ttk.Entry(container, show="*")
        self.pw2.pack(fill="x", pady=(0, 8))

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Change", command=self.change_password).pack(side="left")
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")

    def change_password(self):
        username = self.user_var.get().strip()
        pw = self.pw.get()
        pw2 = self.pw2.get()
        if not username:
            messagebox.showwarning("Missing user", "Select a user.")
            return
        if not pw:
            messagebox.showwarning("Missing password", "Enter a new password.")
            return
        if pw != pw2:
            messagebox.showerror("Mismatch", "Passwords do not match.")
            return
        try:
            repo.update_user_password(username, pw)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not change password:\n{exc}")
            return
        messagebox.showinfo("Success", "Password changed successfully.")
        self.destroy()
 


class Dashboard(ttk.Frame):
    def __init__(self, master: tk.Tk, username: str):
        super().__init__(master, padding=12)
        self.master = master
        self.username = username
        self.selected_client_id: int | None = None
        self.current_client_id: int | None = None

        self.configure(style="App.TFrame")
        self.pack(fill="both", expand=True)

        self._build_header()
        self._build_nav()
        self._build_screens()

        self.show_screen("ledger")
        self.refresh_all()

    def _build_header(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 16))
        header.pack(fill="x", pady=(0, 10))
        left = ttk.Frame(header, style="Header.TFrame")
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Client Ledger Desk", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(left, text=f"Logged in as {self.username}", style="HeaderSub.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Button(header, text="Reset Database", command=self.reset_database).pack(side="right")
        ttk.Button(header, text="Change Password", command=self.open_change_password).pack(side="right", padx=(0, 8))
        ttk.Button(header, text="Logout", command=self.logout).pack(side="right")

    def open_change_password(self):
        ChangePasswordDialog(self)

    def _build_nav(self):
        nav = ttk.Frame(self, padding=(4, 2))
        nav.pack(fill="x", pady=(0, 8))
        self.ledger_btn = ttk.Button(nav, text="Ledger Management", command=lambda: self.show_screen("ledger"))
        self.client_btn = ttk.Button(nav, text="Client Management", command=lambda: self.show_screen("client"))
        self.payment_btn = ttk.Button(nav, text="Payment Management", command=lambda: self.show_screen("payment"))
        self.ledger_btn.pack(side="left")
        self.client_btn.pack(side="left", padx=8)
        self.payment_btn.pack(side="left", padx=8)

    def _build_screens(self):
        self.content = ttk.Frame(self, style="Card.TFrame", padding=12)
        self.content.pack(fill="both", expand=True)

        self.ledger_screen = ttk.Frame(self.content, style="Card.TFrame")
        self.client_screen = ttk.Frame(self.content, style="Card.TFrame")
        self.payment_screen = ttk.Frame(self.content, style="Card.TFrame")

        self._build_ledger_screen()
        self._build_client_screen()
        self._build_payment_screen()

    def show_screen(self, name: str):
        self.ledger_screen.pack_forget()
        self.client_screen.pack_forget()
        self.payment_screen.pack_forget()
        if name == "ledger":
            self.ledger_screen.pack(fill="both", expand=True)
        elif name == "client":
            self.client_screen.pack(fill="both", expand=True)
        elif name == "payment":
            self.payment_screen.pack(fill="both", expand=True)
            self.refresh_payment_list()

    def _build_ledger_screen(self):
        ttk.Label(self.ledger_screen, text="Ledger Management", style="Section.TLabel").pack(anchor="w")

        top = ttk.Frame(self.ledger_screen)
        top.pack(fill="x", pady=(10, 8))

        ttk.Label(top, text="Client Filter").pack(side="left")
        self.ledger_filter = tk.StringVar()
        self.ledger_filter_combo = ttk.Combobox(top, textvariable=self.ledger_filter, state="readonly", width=38)
        self.ledger_filter_combo.pack(side="left", padx=8)
        self.ledger_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_ledger_list())

        ttk.Button(top, text="Add Ledger", command=self.open_add_ledger_modal).pack(side="left", padx=(10, 0))
        ttk.Button(top, text="Export", command=self.export_selected_client).pack(side="left", padx=(8, 0))
        ttk.Button(top, text="Refresh", command=self.refresh_ledger_list).pack(side="right")

        self.ledger_total_label = ttk.Label(self.ledger_screen, text="Client total amount: 0.00", style="Info.TLabel")
        self.ledger_total_label.pack(anchor="w", pady=(0, 8))

        # Info labels for buyer/seller
        self.ledger_info_frame = ttk.Frame(self.ledger_screen)
        self.ledger_info_frame.pack(anchor="w", pady=(0, 8))
        self.ledger_amount_label = ttk.Label(self.ledger_info_frame, text="", style="Info.TLabel")
        self.ledger_amount_label.pack(anchor="w")
        self.ledger_payment_label = ttk.Label(self.ledger_info_frame, text="", style="Info.TLabel")
        self.ledger_payment_label.pack(anchor="w")
        self.ledger_remaining_label = ttk.Label(self.ledger_info_frame, text="", style="Info.TLabel")
        self.ledger_remaining_label.pack(anchor="w")

        columns = ("id", "client", "product", "quantity", "price", "total", "created")
        self.ledger_tree = ttk.Treeview(self.ledger_screen, columns=columns, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 40),
            ("client", "Client", 140),
            ("product", "Product", 100),
            ("quantity", "Qty (kg)", 80),
            ("price", "Price/kg", 80),
            ("total", "Total", 90),
            ("created", "Created (Bengali)", 150),
        ]:
            self.ledger_tree.heading(col, text=title)
            self.ledger_tree.column(col, width=width, anchor="w")
        ledger_x_scroll = ttk.Scrollbar(self.ledger_screen, orient="horizontal", command=self.ledger_tree.xview)
        self.ledger_tree.configure(xscrollcommand=ledger_x_scroll.set)
        self.ledger_tree.pack(fill="both", expand=True)
        ledger_x_scroll.pack(fill="x")

    def _build_client_screen(self):
        ttk.Label(self.client_screen, text="Client Management", style="Section.TLabel").pack(anchor="w")

        search_row = ttk.Frame(self.client_screen)
        search_row.pack(fill="x", pady=(10, 8))
        self.client_search = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.client_search).pack(side="left", fill="x", expand=True)
        ttk.Button(search_row, text="Search", command=self.refresh_clients).pack(side="left", padx=6)
        ttk.Button(search_row, text="Refresh", command=self.refresh_clients).pack(side="left")

        columns = ("id", "name", "type", "phone", "email", "total")
        self.client_tree = ttk.Treeview(self.client_screen, columns=columns, show="headings", height=10)
        for col, title, width in [
            ("id", "ID", 50),
            ("name", "Name", 140),
            ("type", "Type", 70),
            ("phone", "Phone", 110),
            ("email", "Email", 220),
            ("total", "Total Amount", 100),
        ]:
            self.client_tree.heading(col, text=title)
            self.client_tree.column(col, width=width, anchor="w")
        self.client_tree.bind("<<TreeviewSelect>>", self.on_client_selected)
        self.client_tree.pack(fill="both", expand=True)

        form = ttk.LabelFrame(self.client_screen, text="Add / Update Client", padding=12)
        form.pack(fill="x", pady=12)
        for i in range(2):
            form.columnconfigure(i, weight=1)

        self.client_name = tk.StringVar()
        self.client_phone = tk.StringVar()
        self.client_email = tk.StringVar()
        self.client_type = tk.StringVar(value="buyer")

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.client_name).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))
        ttk.Label(form, text="Phone").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.client_phone).grid(row=1, column=1, sticky="ew", pady=(0, 8))
        ttk.Label(form, text="Email").grid(row=2, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.client_email).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(form, text="Client Type").grid(row=4, column=0, sticky="w")
        ttk.Combobox(form, textvariable=self.client_type, values=["buyer", "seller"], state="readonly").grid(row=4, column=1, sticky="ew", pady=(0, 8))

        actions = ttk.Frame(form)
        actions.grid(row=5, column=0, columnspan=2, sticky="ew")
        ttk.Button(actions, text="Save Client", command=self.save_client).pack(side="left")
        ttk.Button(actions, text="Clear", command=self.clear_client_form).pack(side="left", padx=8)
        ttk.Button(actions, text="Delete", command=self.delete_selected_client).pack(side="left", padx=8)

    def _build_payment_screen(self):
        ttk.Label(self.payment_screen, text="Payment Management", style="Section.TLabel").pack(anchor="w")

        top = ttk.Frame(self.payment_screen)
        top.pack(fill="x", pady=(10, 8))

        ttk.Label(top, text="Client Filter").pack(side="left")
        self.payment_filter = tk.StringVar()
        self.payment_filter_combo = ttk.Combobox(top, textvariable=self.payment_filter, state="readonly", width=38)
        self.payment_filter_combo.pack(side="left", padx=8)
        self.payment_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_payment_list())

        ttk.Button(top, text="Add Payment", command=self.open_add_payment_modal).pack(side="left", padx=(10, 0))
        ttk.Button(top, text="Refresh", command=self.refresh_payment_list).pack(side="right")

        self.payment_info_label = ttk.Label(self.payment_screen, text="", style="Info.TLabel")
        self.payment_info_label.pack(anchor="w", pady=(0, 8))

        columns = ("id", "client", "amount", "mode", "created")
        self.payment_tree = ttk.Treeview(self.payment_screen, columns=columns, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 50),
            ("client", "Client", 170),
            ("amount", "Amount", 100),
            ("mode", "Payment Mode", 120),
            ("created", "Created (Bengali)", 180),
        ]:
            self.payment_tree.heading(col, text=title)
            self.payment_tree.column(col, width=width, anchor="w")
        
        # Add delete functionality
        def delete_selected_payment():
            selection = self.payment_tree.selection()
            if not selection:
                messagebox.showwarning("Select payment", "Choose a payment to delete.")
                return
            if messagebox.askyesno("Confirm delete", "Delete this payment record?"):
                values = self.payment_tree.item(selection[0], "values")
                payment_id = int(values[0])
                try:
                    repo.delete_payment(payment_id)
                    self.refresh_payment_list()
                    messagebox.showinfo("Deleted", "Payment record deleted successfully.")
                except Exception as exc:
                    messagebox.showerror("Delete failed", str(exc))
        
        self.payment_tree.bind("<Delete>", lambda e: delete_selected_payment())
        
        payment_x_scroll = ttk.Scrollbar(self.payment_screen, orient="horizontal", command=self.payment_tree.xview)
        self.payment_tree.configure(xscrollcommand=payment_x_scroll.set)
        self.payment_tree.pack(fill="both", expand=True)
        payment_x_scroll.pack(fill="x")

    def logout(self):
        self.destroy()
        LoginWindow(self.master, self._open_dashboard)

    def _open_dashboard(self, username: str):
        Dashboard(self.master, username)

    def refresh_all(self):
        self.refresh_clients()
        self.sync_client_filter()
        self.sync_payment_filter()
        self.refresh_ledger_list()

    def get_client_combo_values(self) -> list[str]:
        clients = repo.list_clients()
        return [f"{item['id']} - {item['name']}" for item in clients]

    def sync_client_filter(self):
        values = ["All Clients"] + self.get_client_combo_values()
        self.ledger_filter_combo["values"] = values

        if self.current_client_id:
            client = repo.get_client(self.current_client_id)
            if client:
                self.ledger_filter.set(f"{client['id']} - {client['name']}")
                return

        if not self.ledger_filter.get() and values:
            self.ledger_filter.set(values[0])

    def _filter_client_id(self) -> int | None:
        value = self.ledger_filter.get().strip()
        if not value or value == "All Clients":
            return None
        try:
            return int(value.split(" - ", 1)[0])
        except ValueError:
            return None

    def refresh_ledger_list(self):
        for item in self.ledger_tree.get_children():
            self.ledger_tree.delete(item)

        selected_client = self._filter_client_id()
        self.current_client_id = selected_client

        rows = repo.list_ledgers_client_wise(selected_client)
        for row in rows:
            self.ledger_tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["client_name"],
                    row.get("product_name", ""),
                    row["quantity_kg"],
                    row["price_per_kg"],
                    f"{row['total_price']:.2f}",
                    repo.utc_to_bengali_date(row["created_at"]),
                ),
            )

        if selected_client:
            client = repo.get_client(selected_client)
            if client:
                client_type = client.get("client_type", "buyer").lower()
                total_paid = client.get("amount_paid", 0)
                remaining = client['total_amount'] - total_paid
                
                self.ledger_total_label.config(text=f"Client: {client['name']} ({client_type.capitalize()})")
                self.ledger_amount_label.config(text=f"Total Amount: {client['total_amount']:.2f}")
                self.ledger_payment_label.config(text=f"Amount Paid: {total_paid:.2f}")
                self.ledger_remaining_label.config(text=f"Remaining: {remaining:.2f}")
            else:
                self.ledger_total_label.config(text="Client not found")
                self.ledger_amount_label.config(text="")
                self.ledger_payment_label.config(text="")
                self.ledger_remaining_label.config(text="")
        else:
            self.ledger_total_label.config(text="Select a client to view details")
            self.ledger_amount_label.config(text="")
            self.ledger_payment_label.config(text="")
            self.ledger_remaining_label.config(text="")

    def refresh_clients(self):
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)

        clients = repo.list_clients(self.client_search.get())
        for client in clients:
            self.client_tree.insert(
                "",
                "end",
                values=(client["id"], client["name"], client["client_type"], client["phone"], client["email"], f"{client['total_amount']:.2f}"),
            )

    def on_client_selected(self, _event=None):
        selection = self.client_tree.selection()
        if not selection:
            return
        values = self.client_tree.item(selection[0], "values")
        if not values:
            return

        client_id = int(values[0])
        client = repo.get_client(client_id)
        if not client:
            return

        self.selected_client_id = client_id
        self.client_name.set(client["name"])
        self.client_phone.set(client["phone"])
        self.client_email.set(client["email"])
        self.client_type.set(client.get("client_type", "buyer"))

    def save_client(self):
        name = self.client_name.get().strip()
        phone = self.client_phone.get().strip()
        email = self.client_email.get().strip()
        client_type = self.client_type.get().strip()

        if not name or not phone or not email:
            messagebox.showwarning("Missing data", "Fill name, phone, and email.")
            return

        try:
            if self.selected_client_id:
                repo.update_client(self.selected_client_id, name, phone, email, client_type)
            else:
                repo.create_client(name, phone, email, client_type)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.clear_client_form()
        self.refresh_all()
        messagebox.showinfo("Saved", "Client saved successfully.")

    def clear_client_form(self):
        self.selected_client_id = None
        self.client_name.set("")
        self.client_phone.set("")
        self.client_email.set("")
        self.client_type.set("buyer")
        self.client_tree.selection_remove(self.client_tree.selection())

    def delete_selected_client(self):
        if not self.selected_client_id:
            messagebox.showinfo("Select client", "Choose a client first.")
            return
        if not messagebox.askyesno("Confirm delete", "Delete this client and all active ledger records?"):
            return
        repo.delete_client(self.selected_client_id)
        self.clear_client_form()
        self.refresh_all()

    def reset_database(self):
        if not messagebox.askyesno(
            "Confirm reset",
            "This will delete all users, clients, and ledgers. Continue?",
        ):
            return

        repo.clear_database()
        messagebox.showinfo("Database cleared", "All records were deleted. Register a new user to continue.")
        self.destroy()
        LoginWindow(self.master, self._open_dashboard)

    def open_add_ledger_modal(self):
        if not self.get_client_combo_values():
            messagebox.showwarning("No clients", "Please add a client first.")
            return
        LedgerEntryModal(self)

    def export_selected_client(self):
        client_id = self._filter_client_id()
        if not client_id:
            messagebox.showwarning("Select client", "Choose a client in Ledger filter before export.")
            return

        buffer = repo.export_client_ledgers(client_id)
        if buffer is None:
            messagebox.showinfo("No record found", "No record found for this client.")
            return

        client = repo.get_client(client_id)
        ts = datetime.now(repo.IST).strftime("%Y-%m-%d_%H%M%S")
        if client and client.get("name"):
            default_name = f"{client['name'].replace(' ', '_')}_ledger_{ts}.xlsx"
        else:
            default_name = f"client_{client_id}_ledger_{ts}.xlsx"

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not path:
            return

        with open(path, "wb") as handle:
            handle.write(buffer.getvalue())

        repo.clear_client_ledgers(client_id)
        self.refresh_all()
        messagebox.showinfo("Exported", f"Ledger exported to:\n{path}")

    def _filter_payment_client_id(self) -> int | None:
        value = self.payment_filter.get().strip()
        if not value or value == "All Clients":
            return None
        try:
            return int(value.split(" - ", 1)[0])
        except ValueError:
            return None

    def sync_payment_filter(self):
        values = ["All Clients"] + self.get_client_combo_values()
        self.payment_filter_combo["values"] = values
        if not self.payment_filter.get() and values:
            self.payment_filter.set(values[0])

    def refresh_payment_list(self):
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)

        selected_client = self._filter_payment_client_id()
        payments = repo.list_payments(selected_client)
        
        total_amount = 0.0
        for payment in payments:
            total_amount += payment["amount"]
            self.payment_tree.insert(
                "",
                "end",
                values=(
                    payment["id"],
                    payment["client_name"],
                    f"{payment['amount']:.2f}",
                    payment["payment_mode"],
                    repo.utc_to_bengali_date(payment["created_at"]),
                ),
            )

        if selected_client:
            client = repo.get_client(selected_client)
            if client:
                remaining = client['total_amount'] - client['amount_paid']
                self.payment_info_label.config(
                    text=f"Total: {client['total_amount']:.2f} | Paid: {client['amount_paid']:.2f} | Remaining: {remaining:.2f}"
                )
            else:
                self.payment_info_label.config(text="")
        else:
            self.payment_info_label.config(text=f"Total Payments: {total_amount:.2f}")

    def open_add_payment_modal(self):
        if not self.get_client_combo_values():
            messagebox.showwarning("No clients", "Please add a client first.")
            return
        PaymentEntryModal(self)


class PaymentEntryModal(tk.Toplevel):
    def __init__(self, parent: "Dashboard"):
        super().__init__(parent.master)
        self.parent = parent

        self.title("Add Payment")
        self.geometry("480x380")
        self.resizable(False, False)
        self.transient(parent.master)
        self.grab_set()

        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=False)

        ttk.Label(container, text="Add Payment", style="Section.TLabel").pack(anchor="w")

        form = ttk.Frame(container)
        form.pack(fill="x", pady=(10, 8))

        ttk.Label(form, text="Client").pack(anchor="w", pady=(0, 4))
        self.client_choice = tk.StringVar()
        self.client_combo = ttk.Combobox(form, textvariable=self.client_choice, state="readonly", width=40)
        self.client_combo.pack(fill="x", pady=(0, 12))
        self.client_combo["values"] = self.parent.get_client_combo_values()
        if self.client_combo["values"]:
            self.client_combo.current(0)

        ttk.Label(form, text="Amount").pack(anchor="w", pady=(0, 4))
        self.amount = ttk.Entry(form)
        self.amount.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Payment Mode").pack(anchor="w", pady=(0, 4))
        self.payment_mode = ttk.Entry(form)
        self.payment_mode.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Date").pack(anchor="w", pady=(0, 4))
        self.selected_date = tk.StringVar(value=datetime.now(repo.IST).strftime("%Y-%m-%d"))
        date_frame = ttk.Frame(form)
        date_frame.pack(fill="x", pady=(0, 12))
        self.date_label = ttk.Label(date_frame, text="Date: " + self.selected_date.get())
        self.date_label.pack(side="left", fill="x", expand=True)
        
        def open_calendar():
            try:
                tkcalendar = importlib.import_module("tkcalendar")
            except ImportError:
                messagebox.showerror("Missing dependency", "Install tkcalendar to use the date picker.")
                return

            cal_window = tk.Toplevel(date_frame)
            cal_window.title("Select Date")
            
            # Parse the current selected date and set it in the calendar
            current_date = datetime.strptime(self.selected_date.get(), "%Y-%m-%d").date()
            cal = tkcalendar.DateEntry(cal_window, width=12, background="darkblue", foreground="white", borderwidth=2, year=current_date.year, month=current_date.month, day=current_date.day)
            cal.pack(padx=10, pady=10)

            def select_date():
                selected = cal.get_date()
                self.selected_date.set(str(selected))
                self.date_label.config(text="Date: " + str(selected))
                cal_window.destroy()

            ttk.Button(cal_window, text="OK", command=select_date).pack(padx=10, pady=5)
        
        ttk.Button(date_frame, text="📅", command=open_calendar).pack(side="left", padx=(4, 0))

        buttons = ttk.Frame(container)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Save Payment", command=self.save_payment).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")

    def selected_client_id(self) -> int | None:
        value = self.client_choice.get().strip()
        if not value:
            return None
        try:
            return int(value.split(" - ", 1)[0])
        except ValueError:
            return None

    def save_payment(self):
        client_id = self.selected_client_id()
        if not client_id:
            messagebox.showwarning("Missing client", "Select a client.")
            return

        try:
            amount = float(self.amount.get().strip())
        except ValueError:
            messagebox.showerror("Invalid data", "Amount must be numeric.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid data", "Amount must be greater than zero.")
            return

        payment_mode = self.payment_mode.get().strip()
        if not payment_mode:
            messagebox.showerror("Missing data", "Enter a payment mode.")
            return

        created_at = self.selected_date.get() + "T00:00:00"

        try:
            repo.create_payment(client_id, amount, payment_mode, created_at)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.parent.sync_payment_filter()
        self.parent.refresh_payment_list()
        messagebox.showinfo("Saved", "Payment record added successfully.")
        self.destroy()
