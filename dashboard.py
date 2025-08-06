import streamlit as st
from modules.auth import check_password
from modules.supabase_db import load_transactions, load_tags
from modules.ui import (
    render_overview_tab,
    render_transaction_tab,
    render_budget_tab,
    render_database_tab,
)

# --- Authenticate ---
check_password()

# --- Load shared data ---
tags = load_tags()
df = load_transactions()

# --- Streamlit Config ---
st.set_page_config(page_title="tpbt", layout="wide")
st.title("tp budget tracker")

# --- Initialize Default Tags (if missing) ---
if not tags:
    tags = {
        "rent": "#FF6B6B",
        "food": "#6BCB77",
        "utils": "#4D96FF",
        "wifey": "#FFB347",
        "personal": "#A66DD4",
        "health": "#FF7F50",
        "subscriptions": "#20B2AA",
        "miscellaneous": "#A9A9A9",
    }
    from modules.supabase_db import insert_or_update_tag
    for name, color in tags.items():
        insert_or_update_tag(name, color)

# --- Setup Tabs ---
tab0, tab1, tab2, tab3 = st.tabs(["overview", "transactions", "budget", "database"])

# --- Render Each Tab ---
with tab0:
    render_overview_tab()

with tab1:
    render_transaction_tab(df)

with tab2:
    render_budget_tab(df, tags)

with tab3:
    render_database_tab(tags)