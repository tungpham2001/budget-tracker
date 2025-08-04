from db import create_tables, create_connection
import datetime

def add_transaction():
    conn = create_connection()
    cursor = conn.cursor()

    date = input("enter date (YYYY-MM-DD): ").strip()
    category = input("enter category (e.g. rent, food,...): ").strip()
    description = input("enter description: ").strip()
    amount = float(input("enter amount: ").strip())
    type_ = input("enter type (income/expense): ").strip().capitalize()

    cursor.execute("""
        INSERT INTO transactions (date, category, description, amount, type)
        VALUES (?, ?, ?, ?, ?)
    """, (date, category, description, amount, type_))

    conn.commit()
    conn.close()
    print("✅ transaction added!")

def view_all_transactions():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()
    print("\n--- all transactions ---")
    for row in rows:
        print(row)
    conn.close()

def add_budget():
    conn = create_connection()
    cursor = conn.cursor()

    month = input("enter month (yyyy-mm): ").strip()
    category = input("enter category (e.g. food, rent): ").strip()
    amount = float(input("enter budgeted amount: ").strip())

    cursor.execute("""
        INSERT INTO budgets (month, category, budgeted_amount)
        VALUES (?, ?, ?)
    """, (month, category, amount))

    conn.commit()
    conn.close()
    print("✅ budget added!")

def view_all_budgets():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets ORDER BY month DESC")
    rows = cursor.fetchall()
    print("\n--- all budgets ---")
    for row in rows:
        print(row)
    conn.close()

def menu():
    while True:
        print("\n=== personal finance CLI ===")
        print("1. add transaction")
        print("2. view all transactions")
        print("3. add budget")
        print("4. view all budgets")
        print("5. exit")
        choice = input("choose an option: ").strip()

        if choice == '1':
            add_transaction()
        elif choice == '2':
            view_all_transactions()
        elif choice == '3':
            add_budget()
        elif choice == '4':
            view_all_budgets()
        elif choice == '5':
            print("goodbye!")
            break
        else:
            print("invalid choice, try again.")

if __name__ == "__main__":
    create_tables()
    menu()
