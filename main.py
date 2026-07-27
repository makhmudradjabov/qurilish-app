"""
Qurilish xarajatlari daftari - backend server
Ishga tushirish: uvicorn main:app --reload
"""
import hashlib
import os
import secrets
import sqlite3
import uuid
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

# ---------------------------------------------------------------------------
# Foydalanuvchilar. Parolni shu yerda o'zgartirishingiz mumkin.
# role: "admin" - hammani ko'radi, "member" - faqat o'zinikini.
# ---------------------------------------------------------------------------
USERS = {
    "Temur": {"password": "7421", "role": "admin"},
    "Suhrob": {"password": "3184", "role": "member"},
    "Kamoladdin": {"password": "5902", "role": "member"},
    "Siroj": {"password": "6637", "role": "member"},
}

SALT = "qurilish-daftari-v1"  # parolni xeshlashda ishlatiladi


def hash_password(password: str) -> str:
    return hashlib.sha256((SALT + password).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Ma'lumotlar bazasi
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS houses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            status TEXT NOT NULL DEFAULT 'faol',
            created_by TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            house_id TEXT NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            added_by TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL
        )"""
    )
    conn.commit()
    conn.close()


init_db()

app = FastAPI(title="Qurilish xarajatlari daftari")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Autentifikatsiya
# ---------------------------------------------------------------------------
class LoginBody(BaseModel):
    name: str
    password: str


class HouseBody(BaseModel):
    name: str


class ExpenseBody(BaseModel):
    houseId: str
    date: str
    category: str
    amount: float
    note: Optional[str] = ""


def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Kirish talab qilinadi")
    token = authorization.replace("Bearer ", "").strip()
    conn = get_db()
    row = conn.execute("SELECT username FROM sessions WHERE token = ?", (token,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(401, "Sessiya tugagan, qayta kiring")
    username = row["username"]
    if username not in USERS:
        raise HTTPException(401, "Foydalanuvchi topilmadi")
    return {"name": username, "role": USERS[username]["role"]}


@app.post("/api/login")
def login(body: LoginBody):
    user = USERS.get(body.name)
    if not user or not secrets.compare_digest(hash_password(body.password), hash_password(user["password"])):
        raise HTTPException(401, "Ism yoki kod noto'g'ri")
    token = str(uuid.uuid4())
    conn = get_db()
    conn.execute("INSERT INTO sessions (token, username) VALUES (?, ?)", (token, body.name))
    conn.commit()
    conn.close()
    return {"token": token, "name": body.name, "role": user["role"]}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


# ---------------------------------------------------------------------------
# Uylar
# ---------------------------------------------------------------------------
@app.get("/api/houses")
def list_houses(user=Depends(current_user)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM houses ORDER BY start_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/houses")
def create_house(body: HouseBody, user=Depends(current_user)):
    hid = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO houses (id, name, start_date, status, created_by) VALUES (?, ?, ?, 'faol', ?)",
        (hid, body.name, str(date.today()), user["name"]),
    )
    conn.commit()
    conn.close()
    return {"id": hid}


def require_admin(user):
    if user["role"] != "admin":
        raise HTTPException(403, "Faqat admin bajara oladi")


@app.post("/api/houses/{house_id}/finish")
def finish_house(house_id: str, user=Depends(current_user)):
    require_admin(user)
    conn = get_db()
    conn.execute(
        "UPDATE houses SET status = 'tugallangan', end_date = ? WHERE id = ?",
        (str(date.today()), house_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/houses/{house_id}/reopen")
def reopen_house(house_id: str, user=Depends(current_user)):
    require_admin(user)
    conn = get_db()
    conn.execute("UPDATE houses SET status = 'faol', end_date = NULL WHERE id = ?", (house_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/houses/{house_id}")
def delete_house(house_id: str, user=Depends(current_user)):
    require_admin(user)
    conn = get_db()
    conn.execute("DELETE FROM houses WHERE id = ?", (house_id,))
    conn.execute("DELETE FROM expenses WHERE house_id = ?", (house_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Xarajatlar
# ---------------------------------------------------------------------------
@app.get("/api/expenses")
def list_expenses(user=Depends(current_user)):
    conn = get_db()
    if user["role"] == "admin":
        rows = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE added_by = ? ORDER BY date DESC", (user["name"],)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/expenses")
def create_expense(body: ExpenseBody, user=Depends(current_user)):
    eid = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (id, house_id, date, category, amount, note, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (eid, body.houseId, body.date, body.category, body.amount, body.note or "", user["name"]),
    )
    conn.commit()
    conn.close()
    return {"id": eid}


@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: str, user=Depends(current_user)):
    conn = get_db()
    row = conn.execute("SELECT added_by FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Topilmadi")
    if row["added_by"] != user["name"]:
        conn.close()
        raise HTTPException(403, "Faqat o'zingiz qo'shgan xarajatni o'chira olasiz")
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Frontend (static fayllar)
# ---------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
