import streamlit as st
import datetime
import pandas as pd
import altair as alt
from modules.supabase_db import (
    load_transactions, insert_transaction, update_transaction, delete_transaction,
    load_budget, insert_budget, update_budget,
    load_tags, insert_or_update_tag, update_tag,
    get_table_data, delete_row, get_all_budget_months, get_all_transaction_months
)
import time

# --- Overview Tab ---
def render_overview_tab():
    df = load_transactions()
    if df.empty:
        return

    selected_month = st.selectbox("select month to view", sorted(get_all_transaction_months(), reverse=True))
    month_data = df[df['month'] == selected_month]

    income = month_data[month_data['type'] == 'income']['amount'].sum()
    expenses = month_data[month_data['type'] == 'expense']['amount'].sum()
    net_left = income - expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("how much i made", f"${income:,.2f}")
    col2.metric("how much i've spent", f"${expenses:,.2f}")
    col3.metric("how much i have left", f"${net_left:,.2f}", delta=f"{net_left:,.2f}")

    st.subheader("budget progress")
    budget_df = load_budget(selected_month)

    if budget_df.empty:
        st.info("no budget set for this month.")
    else:
        budget_df = (
            budget_df.rename(columns={"amount": "budgeted_amount"})
                    .groupby('category', as_index=False)['budgeted_amount']
                    .sum()
        )
        actuals = (
            month_data[month_data['type'].str.lower() == 'expense']
            .groupby('category')['amount']
            .sum()
            .reset_index()
            .rename(columns={'amount': 'actual_spent'})
        )
        progress_df = pd.merge(budget_df, actuals, on='category', how='left')
        progress_df['actual_spent'] = progress_df['actual_spent'].fillna(0)

        for _, row in progress_df.iterrows():
            spent = row['actual_spent']
            budget = row['budgeted_amount']
            percent_used = spent / budget if budget > 0 else 0
            percent_spent = min(percent_used, 1.0)
            percent_left = max(1.0 - percent_spent, 0) * 100

            if percent_used > 1:
                emoji = "⛔"
                percent_over = (percent_used - 1.0) * 100
                label = (
                    f"{emoji} {row['category']}: "
                    f"&#36;{spent:,.2f} of &#36;{budget:,.2f} spent "
                    f"(<span style='color:red;'>{percent_over:.0f}% OVER</span>)"
                )
            elif percent_used >= 0.75:
                emoji = "⚠️"
                label = (
                    f"{emoji} {row['category']}: "
                    f"&#36;{spent:,.2f} of &#36;{budget:,.2f} spent ({percent_left:.0f}% left)"
                )
            else:
                emoji = "✅"
                label = (
                    f"{emoji} {row['category']}: "
                    f"&#36;{spent:,.2f} of &#36;{budget:,.2f} spent ({percent_left:.0f}% left)"
                )

            st.markdown(label, unsafe_allow_html=True)
            st.progress(percent_spent)

    st.subheader("expense breakdown")
    breakdown = (
        month_data[month_data['type'] == 'expense']
        .groupby('category')['amount']
        .sum()
        .reset_index()
        .sort_values(by='amount', ascending=False)
    )

    if not breakdown.empty:
        bar = alt.Chart(breakdown).mark_bar().encode(
            x=alt.X('category:N', sort='-y', axis=alt.Axis(labelAngle=0), title="category"),
            y=alt.Y('amount:Q', title="amount (CAD)"),
            tooltip=['category', 'amount']
        ).properties(width=700, height=400)
        st.altair_chart(bar, use_container_width=True)
    else:
        st.info("no expenses recorded for this month.")

def render_transaction_tab(df):
    st.subheader("add new transaction")
    tags = load_tags()

    with st.form("add_transaction_form"):
        col1, col2 = st.columns(2)
        date = col1.date_input("date")
        category = col2.selectbox("category", list(tags.keys()))

        description = st.text_input("description", placeholder="optional")
        amount = st.number_input("amount", min_value=0.0, format="%.2f")
        type_ = st.selectbox("type", ["expense", "income"])

        submitted = st.form_submit_button("add transaction")

        if submitted:
            response = insert_transaction({
                "date": str(date),
                "category": category.strip(),
                "description": description.strip(),
                "amount": amount,
                "type": type_
            })

            if not response.data:
                st.error(f"supabase error: {response.error.message}")
            else:
                st.success("✅ transaction added!")
                time.sleep(1)
                st.rerun()

    st.subheader("manage categories")

    if tags:
        tag_html = "".join([
            f"""<span style="
                display:inline-block;
                background-color:{color};
                color:#fff;
                padding:4px 12px;
                border-radius:20px;
                font-size:0.85em;
                margin-right:8px;
                margin-bottom:6px;
                white-space:nowrap;
            ">{name}</span>"""
            for name, color in tags.items()
        ])

        st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:4px; margin-top:5px;'>{tag_html}</div>", unsafe_allow_html=True)
    else:
        st.info("no categories added yet.")

    with st.form("add_tag_form"):
        new_tag = st.text_input("new category")
        new_color = st.color_picker("color", "#000000")
        tag_submit = st.form_submit_button("add category")

        if tag_submit and new_tag:
            insert_or_update_tag(new_tag.strip(), new_color)
            st.success(f"✅ category '{new_tag}' added!")
            time.sleep(1)
            st.rerun()

    if df.empty:
        st.warning("no transactions to display.")
    else:
        st.subheader("all transactions")
        df['date'] = pd.to_datetime(df['date'])
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        min_amount = float(df['amount'].min())
        max_amount = float(df['amount'].max())

        col1, col2 = st.columns(2)
        with col1:
            date_range = st.date_input("date range", (min_date, max_date))
        with col2:
            st.markdown("**amount range ($)**")
            min_val_input = st.number_input("min", min_value=min_amount, max_value=max_amount, value=min_amount, step=1.0)
            max_val_input = st.number_input("max", min_value=min_val_input, max_value=max_amount, value=max_amount, step=1.0)

        tag_filter = st.multiselect("filter by category", list(tags.keys()))

        filtered = df[
            (df['date'].dt.date >= date_range[0]) &
            (df['date'].dt.date <= date_range[1]) &
            (df['amount'] >= min_val_input) &
            (df['amount'] <= max_val_input)
        ]
        if tag_filter:
            filtered = filtered[filtered['category'].isin(tag_filter)]

        def format_tag(tag):
            color = tags.get(tag, "#DDDDDD")
            return f'<span style="background-color:{color}; color:#fff; padding:2px 10px; border-radius:20px; font-size:0.9em;">{tag}</span>'

        styled_df = filtered[['date', 'category', 'description', 'amount', 'type']].copy()
        styled_df['category'] = styled_df['category'].apply(format_tag)
        styled_table_html = styled_df.to_html(escape=False, index=False)
        styled_table_html_clean = styled_table_html.split('<table')[1]

        st.markdown(
            f"""
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse: collapse;" {styled_table_html_clean}
                </table>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_budget_tab(df, tags):
    st.subheader("monthly budget")

    with st.form("add_budget_form"):
        col1, col2 = st.columns(2)
        now = datetime.datetime.now()
        years = list(range(now.year - 10, now.year + 3))
        months = [f"{i:02d}" for i in range(1, 13)]

        selected_year = col1.selectbox("Year", options=years, index=years.index(now.year))
        selected_month = col2.selectbox("Month", options=months, index=now.month - 1)

        month = f"{selected_year}-{selected_month}"
        category = col2.selectbox("category", options=list(tags.keys()))

        budgeted_amount = st.number_input("budgeted amount", min_value=0.0, format="%.2f")
        budget_submit = st.form_submit_button("add budget")

        if budget_submit:
            response = insert_budget({
                "month": month.strip(),
                "category": category.strip(),
                "amount": budgeted_amount
            })

            if not response.data:
                st.error(f"error saving budget: {response.error.message}")
            else:
                st.success("✅ budget added!")
                time.sleep(1)
                st.rerun()

    if df.empty:
        st.info("no transaction data available to compare with budgets.")
    else:
        month_list = get_all_budget_months()
        month_selected = st.selectbox("select month for budget review", month_list, key="budget_month")
        budget_df = load_budget(month_selected)

        if budget_df.empty:
            st.info("no budget set for this month.")
        else:
            budget_df = (
                budget_df.rename(columns={"amount": "budgeted_amount"})
                        .groupby('category', as_index=False)['budgeted_amount']
                        .sum()
            )

            filtered = df[df['month'] == month_selected]
            actuals = (
                filtered[filtered['type'].str.lower() == 'expense']
                .groupby('category')['amount']
                .sum()
                .reset_index()
                .rename(columns={'amount': 'actual_spent'})
            )

            merged = pd.merge(budget_df, actuals, on='category', how='left')
            merged['actual_spent'] = merged['actual_spent'].fillna(0)
            merged['difference'] = merged['budgeted_amount'] - merged['actual_spent']

            st.subheader(f"budget vs actual – {month_selected}")

            chart_df = merged.melt(id_vars='category', value_vars=['budgeted_amount', 'actual_spent'],
                                var_name='Type', value_name='Amount')

            bar = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('category:N', title='category'),
                y=alt.Y('Amount:Q'),
                color=alt.Color('Type:N', scale=alt.Scale(range=['#4D96FF', '#FF6B6B'])),
                tooltip=['category', 'Type', 'Amount']
            ).properties(
                width=700,
                height=400
            )

            st.altair_chart(bar, use_container_width=True)

            with st.expander("show budget vs actual table"):
                st.dataframe(merged[['category', 'budgeted_amount', 'actual_spent', 'difference']])

def render_database_tab(tags):
    st.subheader("database management")

    table_selection = st.selectbox("select database", ["transactions", "budgets", "tags"])
    primary_key_map = {
        "transactions": "id",
        "budgets": "id",
        "tags": "name"
    }
    pk = primary_key_map[table_selection]
    df = get_table_data(table_selection)

    if df.empty:
        st.info("no data to display.")
        return

    # show column headers
    header_cols = st.columns(len(df.columns) + 1)
    for i, col_name in enumerate(df.columns):
        header_cols[i].markdown(f"**{col_name}**")

    for _, row in df.iterrows():
        with st.container():
            cols = st.columns(len(row) + 1)
            for i, col in enumerate(row.index):
                cols[i].write(row[col])

            action_col1, action_col2 = cols[-1].columns(2)
            edit_key = f"edit_{table_selection}_{row[pk]}"
            delete_key = f"delete_{table_selection}_{row[pk]}"

            if action_col1.button("✏️", key=edit_key):
                st.session_state["edit_target"] = (table_selection, row[pk])
                st.rerun()

            if action_col2.button("🗑️", key=delete_key):
                st.session_state["delete_target"] = (table_selection, row[pk])
                st.rerun()

    # edit handler
    if st.session_state.get("edit_target"):
        table, edit_id = st.session_state["edit_target"]
        edit_df = get_table_data(table)
        edit_row = edit_df[edit_df[pk] == edit_id].iloc[0]

        with st.form("edit_form"):
            st.markdown(f"### edit entry in `{table}`")

            if table == "transactions":
                new_date = st.date_input("date", pd.to_datetime(edit_row['date']))
                new_category = st.selectbox("category", list(tags.keys()), index=list(tags.keys()).index(edit_row['category']) if edit_row['category'] in tags else 0)
                new_desc = st.text_input("description", value=edit_row['description'])
                new_amount = st.number_input("amount", value=edit_row['amount'], format="%.2f")
                new_type = st.selectbox("type", ["expense", "income"], index=0 if edit_row['type'] == "expense" else 1)
            elif table == "budgets":
                new_month = st.text_input("month", value=edit_row['month'])
                new_category = st.selectbox("category", list(tags.keys()), index=list(tags.keys()).index(edit_row['category']) if edit_row['category'] in tags else 0)
                new_amount = st.number_input("budgeted amount", value=edit_row['amount'], format="%.2f")
            else:  # tags
                new_name = st.text_input("category name", value=edit_row['name'])
                new_color = st.color_picker("color", value=edit_row['color'])

            col1, col2 = st.columns(2)
            if col1.form_submit_button("update"):
                if table == "transactions":
                    update_transaction(edit_id, str(new_date), new_category, new_desc, new_amount, new_type)
                elif table == "budgets":
                    update_budget(edit_id, new_month, new_category, new_amount)
                else:
                    update_tag(edit_id, new_name.strip(), new_color)
                st.success("✅ row updated!")
                st.session_state.pop("edit_target")
                time.sleep(1)
                st.rerun()

            if col2.form_submit_button("cancel"):
                st.session_state.pop("edit_target")
                st.rerun()

    # delete handler
    if st.session_state.get("delete_target"):
        table, delete_id = st.session_state["delete_target"]
        st.warning(f"are you sure you want to delete row id {delete_id} from `{table}`?")
        col1, col2 = st.columns(2)

        if col1.button("✅ confirm"):
            delete_row(table, delete_id)
            st.success("✅ row deleted!")
            st.session_state.pop("delete_target")
            time.sleep(1)
            st.rerun()

        if col2.button("❌ cancel"):
            st.session_state.pop("delete_target")
            st.rerun()