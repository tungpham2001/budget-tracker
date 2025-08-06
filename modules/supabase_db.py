import os
import pandas as pd
from supabase import create_client, Client
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Transactions ---
def load_transactions():
    response = supabase.table("transactions").select("*").execute()
    if not response.data:
        st.warning("⚠️ no transactions found or error fetching data.")
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').astype(str)
    return df

def insert_transaction(transaction):
    return supabase.table("transactions").insert(transaction).execute()

def update_transaction(id, date, category, description, amount, type_):
    return supabase.table("transactions").update({
        "date": date,
        "category": category,
        "description": description,
        "amount": amount,
        "type": type_
    }).eq("id", id).execute()

def delete_transaction(id):
    return supabase.table("transactions").delete().eq("id", id).execute()

# --- Budgets ---
def load_budget(month):
    response = supabase.table("budgets").select("*").eq("month", month).execute()
    if not response.data:
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def insert_budget(budget):
    return supabase.table("budgets").insert(budget).execute()

def update_budget(id, month, category, amount):
    return supabase.table("budgets").update({
        "month": month,
        "category": category,
        "amount": amount
    }).eq("id", id).execute()

# --- Tags ---
def load_tags():
    response = supabase.table("tags").select("*").execute()
    if not response.data:
        st.error("error fetching tags.")
        return pd.DataFrame()
    df = pd.DataFrame(response.data)
    return dict(zip(df['name'], df['color']))

def insert_or_update_tag(name, color):
    return supabase.table("tags").upsert({
        "name": name,
        "color": color
    }).execute()

def update_tag(current_name, new_name, new_color):
    return supabase.table("tags").update({
        "name": new_name,
        "color": new_color
    }).eq("name", current_name).execute()

# --- General ---
def get_table_data(name):
    response = supabase.table(name).select("*").execute()
    if not response.data:
        error_msg = "error fetching table data: " + name
        st.error(error_msg)
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def delete_row(table, row_id):
    return supabase.table(table).delete().eq("id", row_id).execute()

def get_all_budget_months():
    response = supabase.table("budgets").select("month").execute()
    if not response.data:
        return []
    return list({entry['month'] for entry in response.data if 'month' in entry})

def get_all_transaction_months():
    df = load_transactions()
    if df.empty or 'month' not in df.columns:
        return []
    return df['month'].dropna().unique().tolist()