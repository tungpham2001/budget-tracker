import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
PASSWORD_HASH = os.environ.get("BUDGET_TRACKER_PASSWORD_HASH")

def check_password():
    def password_entered():
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == PASSWORD_HASH:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("enter password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("enter password", type="password", on_change=password_entered, key="password")
        st.error("❌ incorrect password")
        st.stop()