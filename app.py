import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date
import calendar
from sqlalchemy import func
from sklearn.linear_model import LinearRegression

from models import Session, Expense
from ml_utils import predict_category

st.set_page_config(page_title="Smart Expense Analyzer", layout="wide", page_icon="💸")

# Global CSS for a slightly more polished look within Streamlit
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("💸 Smart Expense Analyzer")

session = Session()

# --- HELPER FUNCTIONS ---
def get_businesses():
    businesses = session.query(Expense.business_name).distinct().all()
    # Always ensure at least one default
    b_list = [b[0] for b in businesses if b[0]]
    if "Main Business" not in b_list:
        b_list.append("Main Business")
    return sorted(b_list)

def get_all_expenses(business_name):
    return session.query(Expense).filter(Expense.business_name == business_name).order_by(Expense.date.desc()).all()

def calculate_prediction(expenses):
    if not expenses:
        return 0.0, "No data to predict."

    expenses_asc = sorted(expenses, key=lambda x: x.date)
    min_date = expenses_asc[0].date
    max_date = expenses_asc[-1].date
    timespan = (max_date - min_date).days + 1
    total_amount = sum(e.amount for e in expenses_asc)

    if timespan < 30:
        daily_avg = total_amount / timespan if timespan > 0 else 0
        predicted_amount = daily_avg * 30
        return predicted_amount, "Extrapolated from daily average (less than 1 month data)."

    monthly_totals = {}
    for e in expenses_asc:
        month_key = e.date.strftime('%Y-%m')
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + e.amount
    
    sorted_months = sorted(monthly_totals.keys())
    
    today = date.today()
    current_month_key = today.strftime('%Y-%m')
    
    if current_month_key in monthly_totals and current_month_key == sorted_months[-1]:
        day_of_month = today.day
        if day_of_month < 28:
            _, days_in_month = calendar.monthrange(today.year, today.month)
            extrapolated = (monthly_totals[current_month_key] / day_of_month) * days_in_month
            monthly_totals[current_month_key] = extrapolated

    if len(monthly_totals) < 2:
        return float(list(monthly_totals.values())[0]), "Need data from multiple months for trend analysis."
        
    def months_since(d_str, origin_str):
        y, m = map(int, d_str.split('-'))
        oy, om = map(int, origin_str.split('-'))
        return (y - oy) * 12 + (m - om)

    origin = sorted_months[0]
    X = np.array([[months_since(m, origin)] for m in sorted_months])
    y = np.array([monthly_totals[m] for m in sorted_months])
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_month_str = sorted_months[-1]
    next_month_idx = months_since(last_month_str, origin) + 1
    
    predicted_amount = float(model.predict([[next_month_idx]])[0])
    
    if len(sorted_months) <= 3:
        avg_monthly = sum(y) / len(y)
        predicted_amount = (predicted_amount + avg_monthly) / 2
    
    if predicted_amount < 0:
        predicted_amount = sum(y) / len(y)
        
    return predicted_amount, "Linear Regression Forecast"

# --- SIDEBAR: BUSINESS SELECTION ---
st.sidebar.header("🏢 Business Profile")

# Get existing businesses
existing_businesses = get_businesses()

# Let user select or create a new business
selected_business = st.sidebar.selectbox("Select Business", existing_businesses)

with st.sidebar.expander("➕ Create New Business Profile"):
    new_biz_name = st.text_input("New Business Name")
    if st.button("Create Profile"):
        if new_biz_name and new_biz_name not in existing_businesses:
            # We add a dummy expense worth 0 to register the name in the DB
            dummy = Expense(amount=0.0, category="Miscellaneous", description="Profile created", business_name=new_biz_name)
            session.add(dummy)
            session.commit()
            st.success(f"Created {new_biz_name}!")
            st.rerun()
        elif new_biz_name in existing_businesses:
            st.warning("Business already exists.")

st.sidebar.markdown("---")

# --- SIDEBAR: ENTRY FORM ---
st.sidebar.header(f"Add Expense: {selected_business}")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date", date.today())
    amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
    description = st.text_input("Description (e.g. Van diesel)")
    
    category = st.selectbox(
        "Category", 
        ["Auto-Classify via AI", "Fuel", "Salary", "Maintenance", "Rent", "Utilities", "Miscellaneous"]
    )
    
    submitted = st.form_submit_button("Add Expense")
    
    if submitted:
        if not description:
            st.error("Please enter a description.")
        else:
            final_cat = category
            if category == "Auto-Classify via AI":
                final_cat = predict_category(description)
                
            new_expense = Expense(
                business_name=selected_business,
                date=expense_date,
                amount=amount,
                category=final_cat,
                description=description
            )
            session.add(new_expense)
            session.commit()
            st.success(f"Added ₹{amount} for {final_cat} in {selected_business}")
            st.rerun() # Refresh data

st.sidebar.markdown("---")
st.sidebar.header("✏️ Edit / Delete Expense")

# Fetch expenses just for the sidebar editing feature
sidebar_expenses = get_all_expenses(selected_business)
sidebar_expenses = [e for e in sidebar_expenses if e.amount > 0]

if sidebar_expenses:
    expense_options = {f"{e.date.strftime('%Y-%m-%d')} - {e.description} (₹{e.amount})": e for e in sidebar_expenses}
    selected_expense_str = st.sidebar.selectbox("Select Expense to Edit", list(expense_options.keys()))
    selected_exp = expense_options[selected_expense_str]
    
    with st.sidebar.form("edit_form"):
        new_date = st.date_input("Edit Date", selected_exp.date)
        new_amount = st.number_input("Edit Amount (₹)", min_value=0.01, step=10.0, value=float(selected_exp.amount), format="%.2f")
        new_desc = st.text_input("Edit Description", selected_exp.description)
        
        cats = ["Fuel", "Salary", "Maintenance", "Rent", "Utilities", "Miscellaneous"]
        idx = cats.index(selected_exp.category) if selected_exp.category in cats else 0
        new_cat = st.selectbox("Edit Category", cats, index=idx)
        
        col1, col2 = st.columns(2)
        update_btn = col1.form_submit_button("Update")
        delete_btn = col2.form_submit_button("Delete")
        
        if update_btn:
            exp_to_upd = session.query(Expense).get(selected_exp.id)
            exp_to_upd.date = new_date
            exp_to_upd.amount = new_amount
            exp_to_upd.description = new_desc
            exp_to_upd.category = new_cat
            session.commit()
            st.success("Expense updated!")
            st.rerun()
            
        if delete_btn:
            exp_to_del = session.query(Expense).get(selected_exp.id)
            session.delete(exp_to_del)
            session.commit()
            st.success("Expense deleted!")
            st.rerun()
else:
    st.sidebar.info("No expenses available to edit.")

st.sidebar.markdown("---")
st.sidebar.subheader("Danger Zone")
confirm_delete = st.sidebar.checkbox(f"I want to delete all data for {selected_business}")
if st.sidebar.button(f"🗑️ Delete {selected_business} Data", disabled=not confirm_delete):
    try:
        session.query(Expense).filter(Expense.business_name == selected_business).delete()
        session.commit()
        st.sidebar.success(f"All data for {selected_business} cleared!")
        st.rerun()
    except Exception as e:
        session.rollback()
        st.sidebar.error(f"Error clearing data: {e}")

# --- MAIN DASHBOARD ---
st.header(f"📊 Dashboard: {selected_business}")
expenses = get_all_expenses(selected_business)
# Filter out the 0.0 dummy expenses used for profile creation
expenses = [e for e in expenses if e.amount > 0]

if not expenses:
    st.info("No expenses recorded yet. Add some using the sidebar menu!")
else:
    # Top KPI Metrics
    total_expense = sum(e.amount for e in expenses)
    predicted_amount, pred_msg = calculate_prediction(expenses)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Recorded Expense", value=f"₹{total_expense:,.2f}")
    with col2:
        st.metric(label="AI Prediction: Next Month", value=f"₹{predicted_amount:,.2f}", help=pred_msg)
        
    # Smart Alerts Logic
    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
        
    if category_totals.get('Fuel', 0) > 4000:
        st.warning("⚠️ **Smart Alert:** Fuel spending is unusually high this month.")
    if category_totals.get('Maintenance', 0) > 1500:
        st.warning("⚠️ **Smart Alert:** Maintenance costs have spiked recently.")

    st.markdown("---")
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Category Breakdown")
        cat_df = pd.DataFrame(list(category_totals.items()), columns=['Category', 'Amount'])
        fig = px.bar(cat_df, x='Category', y='Amount', color='Category', 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
    with chart_col2:
        st.subheader("Recent Spend Trend")
        # Ensure we're grouping by date effectively
        df = pd.DataFrame([e.to_dict() for e in expenses])
        df['date'] = pd.to_datetime(df['date'])
        daily_totals = df.groupby('date')['amount'].sum().reset_index()
        daily_totals = daily_totals.sort_values('date').tail(14) # Last 14 days of data
        
        if not daily_totals.empty:
            fig2 = px.line(daily_totals, x='date', y='amount', markers=True, 
                           line_shape='spline', color_discrete_sequence=['#8b5cf6'])
            fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Date", yaxis_title="Amount")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write("Not enough data to plot a trend.")

    st.markdown("---")
    
    st.subheader("All Transactions")
    # Display dataframe
    st.dataframe(
        df[['date', 'description', 'category', 'amount']].sort_values('date', ascending=False),
        use_container_width=True,
        column_config={
            "date": "Date",
            "description": "Description",
            "category": "Category",
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f")
        },
        hide_index=True
    )

session.close()
