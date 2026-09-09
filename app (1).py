

  
  



    





               
import streamlit as st
from google import genai
import time
import random


st.set_page_config(
    page_title="AI Budget Planner",
    page_icon="💰",
    layout="wide"
)


st.markdown(
    "<h1 style='text-align:center;'>💰 AI Budget Planner</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;'>Plan your salary, control your expenses, and build better saving habits.</p>",
    unsafe_allow_html=True
)


api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()


client = genai.Client(api_key=api_key)


# Stable Gemini 3 models. The first model is the primary choice;
# the others are fallbacks if a model is temporarily unavailable.
MODEL_NAMES = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]


def generate_budget_analysis(prompt):
    """Call Gemini with retries and model fallbacks for transient errors."""
    last_error = None

    for model_name in MODEL_NAMES:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if response and response.text:
                    return response.text, model_name

                last_error = RuntimeError("Gemini returned an empty response.")
                break

            except Exception as e:
                last_error = e
                error_text = str(e).lower()

                # 404/model-not-found: this model is unavailable for this API key.
                # Move immediately to the next stable model.
                is_not_found = (
                    "404" in error_text
                    or "not_found" in error_text
                    or "model_not_found" in error_text
                    or "not found" in error_text
                )

                # 503/429/5xx: transient server or rate-limit problem.
                # Retry with exponential backoff before changing models.
                is_transient = (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "429" in error_text
                    or "resource_exhausted" in error_text
                    or "500" in error_text
                    or "502" in error_text
                    or "504" in error_text
                    or "deadline" in error_text
                    or "timeout" in error_text
                )

                if is_not_found:
                    break

                if is_transient and attempt < 2:
                    delay = (2 ** attempt) + random.uniform(0, 0.75)
                    time.sleep(delay)
                    continue

                # Do not keep retrying permanent client errors.
                break

    raise RuntimeError(
        "Gemini is temporarily unavailable after trying the configured "
        "stable models. Please wait a little and try again."
    ) from last_error


st.header("💵 Monthly Income")

salary = st.number_input(
    "Enter your monthly salary",
    min_value=0.0,
    value=50000.0,
    step=1000.0,
    format="%.0f"
)


st.divider()
st.header("🧾 Monthly Expenses")

col1, col2 = st.columns(2)

with col1:
    rent = st.number_input(
        "🏠 Rent / Housing",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

    food = st.number_input(
        "🍔 Food / Groceries",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    transport = st.number_input(
        "🚗 Transport",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    bills = st.number_input(
        "💡 Bills / Utilities",
        min_value=0.0,
        value=0.0,
        step=500.0
    )


with col2:
    shopping = st.number_input(
        "🛍️ Shopping",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    entertainment = st.number_input(
        "🎬 Entertainment",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    education = st.number_input(
        "📚 Education",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    other = st.number_input(
        "📦 Other Expenses",
        min_value=0.0,
        value=0.0,
        step=500.0
    )


expenses = {
    "Rent / Housing": rent,
    "Food / Groceries": food,
    "Transport": transport,
    "Bills / Utilities": bills,
    "Shopping": shopping,
    "Entertainment": entertainment,
    "Education": education,
    "Other Expenses": other
}


total_expenses = sum(expenses.values())
remaining = salary - total_expenses


st.divider()
st.header("📊 Budget Summary")

c1, c2, c3 = st.columns(3)

c1.metric("Monthly Salary", f"{salary:,.0f}")
c2.metric("Total Expenses", f"{total_expenses:,.0f}")
c3.metric("Remaining", f"{remaining:,.0f}")


if salary > 0:
    st.subheader("📈 Expense Breakdown")

    rows = []

    for name, amount in expenses.items():
        if amount > 0:
            rows.append({
                "Expense": name,
                "Amount": f"{amount:,.0f}",
                "% of Salary": f"{(amount / salary) * 100:.1f}%"
            })

    if rows:
        st.table(rows)

    expense_ratio = (total_expenses / salary) * 100

    if expense_ratio > 100:
        st.error("⚠️ Your expenses are higher than your salary.")

    elif expense_ratio > 80:
        st.warning("⚠️ More than 80% of your salary is being spent.")

    elif expense_ratio > 50:
        st.info("ℹ️ More than half of your salary is going toward expenses.")

    else:
        st.success("✅ Your current expense level leaves room for savings.")


st.divider()
st.header("🤖 AI Budget Analysis")


if st.button("✨ Analyze My Budget", use_container_width=True):

    if salary <= 0:
        st.error("Please enter a valid salary.")
        st.stop()

    expense_text = "\n".join(
        f"- {name}: {amount:,.0f}"
        for name, amount in expenses.items()
        if amount > 0
    )

    if not expense_text:
        st.warning("Please enter at least one expense.")
        st.stop()

    prompt = f"""
You are a professional personal budgeting assistant.

Analyze this monthly budget:

Salary: {salary:,.0f}

Expenses:
{expense_text}

Total Expenses: {total_expenses:,.0f}
Remaining: {remaining:,.0f}

Provide a practical personalized budget.

Use these sections:

## 1. Financial Overview
Explain the user's current financial situation.

## 2. Expense Analysis
Identify high, reasonable, unnecessary, or reducible expenses.
Do not label an expense unnecessary without considering context.

## 3. Priorities
Prioritize essential needs, obligations, savings, wants, and optional expenses.

## 4. Recommended Budget
Suggest realistic amounts for essential expenses, savings,
emergency fund, wants, and flexible spending.
Do not recommend spending more than the salary.

## 5. Savings Recommendation
Suggest a realistic monthly savings amount.

## 6. Expenses to Reduce
Give specific ways to reduce spending where appropriate.

## 7. Action Plan
Give 5 simple actions for next month.

This is general budgeting guidance, not professional financial advice.
"""

    try:
        with st.spinner("🤖 AI is analyzing your budget..."):
            analysis, used_model = generate_budget_analysis(prompt)

        st.success("Your personalized budget analysis is ready!")
        st.markdown(analysis)

    except Exception:
        st.error(
            "Gemini is temporarily busy. Please wait a few seconds and "
            "click **Analyze My Budget** again."
        )

        st.info(
            "The app automatically retries temporary Gemini errors and "
            "tries backup stable models when needed."
        )
