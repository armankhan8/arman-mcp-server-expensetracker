from asyncio import transports
import mimetypes
from fastmcp import FastMCP
import os
import sqlite3

# this is local mcp server 

# making own server and client
# Simply client is cluade desktop and server fastmcp this code, when can simplytell to claude to add something other.

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
categories_path = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ArmanExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # this is for expensis
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        # this is for income realted table:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS income(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool()
def add_income(date, amount, source, note=""):
    """Add a new income entry to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO income(date, amount, source, note) VALUES (?,?,?,?)",
            (date, amount, source, note)
        )
        return {"status": "ok", "id": cur.lastrowid}


# Expenses list    
@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

# Income list
@mcp.tool()
def list_income(start_date, end_date):
    """List income entries within a date range."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT id, date, amount, source, note
            FROM income
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (start_date, end_date))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


mcp.tool()
def summarize_expenses(start_date, end_date, category=None):
    '''Summarize expenses'''
    with sqlite3.connect(DB_PATH) as conn:
        curr = conn.execute('''
        SELECT category, SUM(amount) AS total_amount
        from expenses
        where date between ? and ?
        ''')
        params = [start_date, end_date]
        if category:
            query += " and category = ?"
            params.append(category)
        query += "group by category and order by category asc"
        curr = conn.execute(query)
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols, r)) for r in curr.fetchall()]


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(categories_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def update_expenses(id, date = None, amount = None, category = None, sub_category = None, note = None):
    with sqlite3.connect(DB_PATH) as conn:
        curr = conn.cursor()
        updates = []
        values = []
        for field, val in {
            "date": date,
            "amount": amount, "category": category, "sub_category": sub_category, "note": note
        }.items():
            if val is not None:
                updates.append(f"{field}=?")
                values.append(val)
        if not updates:
            return {"status": "error", "message": "No fields provided to update."}
        values.append(id)
        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id=?"
        curr.execute(query, values)
        conn.commit()
        return {"status": "success", "message": f"Expense with ID {id} updated."}


@mcp.tool()
def delete_expense(id):
    with sqlite3.connect(DB_PATH) as conn:
        curr = conn.cursor()
        curr.execute("Delete from expenses where id = ?", (id, ))
        conn.commit()

    if curr.rowcount == 0:
        return {"status": "error", "message": f"No expense found with ID {id}."}
    else:
        return {"status": "success", "message": f"Expense with ID {id} deleted."}

# get balaance
@mcp.tool()
def get_balance(start_date=None, end_date=None):
    """Calculate total income, total expense, and remaining balance."""
    with sqlite3.connect(DB_PATH) as conn:
        if start_date and end_date:
            income_total = conn.execute(
                "SELECT SUM(amount) FROM income WHERE date BETWEEN ? AND ?", 
                (start_date, end_date)
            ).fetchone()[0] or 0

            expense_total = conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?", 
                (start_date, end_date)
            ).fetchone()[0] or 0
        else:
            income_total = conn.execute("SELECT SUM(amount) FROM income").fetchone()[0] or 0
            expense_total = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0

        balance = income_total - expense_total

        return {
            "total_income": income_total,
            "total_expense": expense_total,
            "balance": balance
        }

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
