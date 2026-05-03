from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .db import get_connection

UTC = timezone.utc
try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    # Fallback for systems missing IANA tz database.
    IST = timezone(timedelta(hours=5, minutes=30))


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def utc_to_ist_string(value: str | None) -> str:
    if not value:
        return ""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return hmac.compare_digest(test, expected)


def create_user(username: str, password: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username.strip(), hash_password(password), now_utc_iso()),
        )
        conn.commit()


def list_users() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username COLLATE NOCASE").fetchall()
    return [row[0] for row in rows]


def update_user_password(username: str, new_password: str) -> None:
    stamp = now_utc_iso()
    hashed = hash_password(new_password)
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE username = ?",
            (hashed, stamp, username.strip()),
        )
        conn.commit()


def authenticate_user(username: str, password: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    if not row:
        return False
    return verify_password(password, row["password_hash"])


def list_clients(search: str = "") -> list[dict]:
    query = "SELECT * FROM clients WHERE deleted_at IS NULL"
    params: list[str] = []
    if search.strip():
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    query += " ORDER BY name COLLATE NOCASE"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_client(client_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ? AND deleted_at IS NULL",
            (client_id,),
        ).fetchone()
    return dict(row) if row else None


def create_client(name: str, phone: str, email: str) -> None:
    stamp = now_utc_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO clients (name, phone, email, total_amount, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (name.strip(), phone.strip(), email.strip(), stamp, stamp),
        )
        conn.commit()


def update_client(client_id: int, name: str, phone: str, email: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE clients
            SET name = ?, phone = ?, email = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (name.strip(), phone.strip(), email.strip(), now_utc_iso(), client_id),
        )
        conn.commit()


def delete_client(client_id: int) -> None:
    stamp = now_utc_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (stamp, stamp, client_id),
        )
        conn.execute(
            "UPDATE ledgers SET deleted_at = ?, updated_at = ? WHERE client_id = ? AND deleted_at IS NULL",
            (stamp, stamp, client_id),
        )
        conn.commit()


def list_ledgers(client_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM ledgers
            WHERE client_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC, id DESC
            """,
            (client_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_ledgers_client_wise(client_id: int | None = None) -> list[dict]:
    query = """
        SELECT l.id, l.client_id, c.name AS client_name, l.quantity_kg, l.price_per_kg,
               l.total_price, l.created_at, l.updated_at
        FROM ledgers l
        JOIN clients c ON c.id = l.client_id
        WHERE l.deleted_at IS NULL AND c.deleted_at IS NULL
    """
    params: list[int] = []
    if client_id is not None:
        query += " AND l.client_id = ?"
        params.append(client_id)
    query += " ORDER BY l.created_at DESC, l.id DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def create_ledgers(client_id: int, entries: Iterable[dict[str, float]]) -> list[dict]:
    entries = list(entries)
    if not entries:
        return []

    stamp = now_utc_iso()
    rows: list[dict] = []
    total_added = 0.0

    with get_connection() as conn:
        for entry in entries:
            qty = float(entry["quantity_kg"])
            price = float(entry["price_per_kg"])
            total_price = qty * price
            total_added += total_price
            cursor = conn.execute(
                """
                INSERT INTO ledgers (client_id, quantity_kg, price_per_kg, total_price, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (client_id, qty, price, total_price, stamp, stamp),
            )
            rows.append(
                {
                    "id": cursor.lastrowid,
                    "client_id": client_id,
                    "quantity_kg": qty,
                    "price_per_kg": price,
                    "total_price": total_price,
                    "created_at": stamp,
                    "updated_at": stamp,
                }
            )

        conn.execute(
            """
            UPDATE clients
            SET total_amount = COALESCE(total_amount, 0) + ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (total_added, stamp, client_id),
        )
        conn.commit()

    return rows


def delete_ledger(ledger_id: int) -> None:
    stamp = now_utc_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE ledgers SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (stamp, stamp, ledger_id),
        )
        conn.commit()


def export_client_ledgers(client_id: int) -> BytesIO | None:
    client = get_client(client_id)
    if not client:
        return None

    ledgers = list_ledgers(client_id)
    if not ledgers:
        return None

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Ledger"

    headers = ["Quantity (kg)", "Price / kg", "Total Price", "Created At (IST)", "Updated At (IST)"]
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center")

    for row in ledgers:
        sheet.append(
            [
                row["quantity_kg"],
                row["price_per_kg"],
                row["total_price"],
                utc_to_ist_string(row["created_at"]),
                utc_to_ist_string(row["updated_at"]),
            ]
        )

    summary = workbook.create_sheet("Summary")
    summary["A1"] = "Client Name"
    summary["B1"] = client["name"]
    summary["A2"] = "Phone"
    summary["B2"] = client["phone"]
    summary["A3"] = "Email"
    summary["B3"] = client["email"]
    summary["A4"] = "Total Amount"
    summary["B4"] = client["total_amount"]
    summary["A5"] = "Exported At (IST)"
    summary["B5"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    for column_cells in sheet.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 22)

    summary.column_dimensions["A"].width = 20
    summary.column_dimensions["B"].width = 40

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return buffer


def clear_client_ledgers(client_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM ledgers WHERE client_id = ?", (client_id,))
        conn.commit()


def clear_database() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM ledgers")
        conn.execute("DELETE FROM clients")
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('ledgers', 'clients', 'users')")
        conn.commit()
