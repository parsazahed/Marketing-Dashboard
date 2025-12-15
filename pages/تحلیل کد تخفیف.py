import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Discount Code Matcher", page_icon="🎫", layout="centered")

st.title("Discount Code Matcher & Analyzer")

# --- HELPER: CLEAN CURRENCY ---
def clean_currency(value):
    """Converts string currency (e.g., '12,000', '۱۲۰۰۰') to float."""
    if pd.isna(value):
        return 0.0
    s = str(value)
    # 1. Replace Persian digits
    farsi = '۰۱۲۳۴۵۶۷۸۹'
    english = '0123456789'
    mapping = str.maketrans(farsi, english)
    s = s.translate(mapping)
    # 2. Remove commas and non-numeric chars (except decimal)
    s = re.sub(r'[^\d.]', '', s)
    try:
        return float(s)
    except:
        return 0.0

# --- STEP 1: UPLOAD ORDERS ---
st.subheader("1. Upload Orders File")
orders_file = st.file_uploader("Upload the main file (Orders)", type=["xlsx", "csv"], key="orders")

df_orders = None
if orders_file:
    try:
        if orders_file.name.endswith('.csv'):
            df_orders = pd.read_csv(orders_file, dtype=str)
        else:
            df_orders = pd.read_excel(orders_file, dtype=str)
        st.success(f"✅ Loaded Orders: {len(df_orders)} rows")
    except Exception as e:
        st.error(f"Error loading orders: {e}")

# --- STEP 2: UPLOAD CODE LIST ---
st.subheader("2. Upload Target Codes")
codes_file = st.file_uploader("Upload the list of codes to find (CSV/Excel)", type=["xlsx", "csv"], key="codes")

df_codes = None
if codes_file:
    try:
        if codes_file.name.endswith('.csv'):
            df_codes = pd.read_csv(codes_file, dtype=str, header=None) 
        else:
            df_codes = pd.read_excel(codes_file, dtype=str, header=None)
        st.success(f"✅ Loaded Code List: {len(df_codes)} rows")
    except Exception as e:
        st.error(f"Error loading codes: {e}")

# --- STEP 3: CONFIGURE & MATCH ---
if df_orders is not None and df_codes is not None:
    st.divider()
    st.subheader("3. Configuration")
    
    col1, col2 = st.columns(2)
    order_cols = df_orders.columns.tolist()
    
    with col1:
        # Match Settings
        st.markdown("##### 🔗 Matching Columns")
        def_ord_idx = 0
        for i, c in enumerate(order_cols):
            if 'کد تخفیف' in str(c) or 'code' in str(c).lower():
                def_ord_idx = i
                break
        target_col_orders = st.selectbox("Column in Orders (Code):", order_cols, index=def_ord_idx)

        # Code List Column
        code_cols = df_codes.columns.tolist()
        target_col_codes = st.selectbox("Column in Code List:", code_cols, format_func=lambda x: f"Column {x+1}")

    with col2:
        # Financial Settings
        st.markdown("##### 💰 Financial Columns")
        
        # Try to auto-find 'Basket item price'
        price_idx = 0
        for i, c in enumerate(order_cols):
            if 'Basket item price' in str(c) or 'price' in str(c).lower():
                price_idx = i
                break
        col_price = st.selectbox("Price Column (Gross Income):", order_cols, index=price_idx)

        # Try to auto-find 'مجموع مبلغ تخفیف'
        discount_idx = 0
        for i, c in enumerate(order_cols):
            if 'مجموع مبلغ تخفیف' in str(c) or 'discount' in str(c).lower():
                discount_idx = i
                break
        col_discount = st.selectbox("Discount Column:", order_cols, index=discount_idx)

    if st.button("🚀 Match & Analyze"):
        # --- A. MATCHING LOGIC ---
        orders_series = df_orders[target_col_orders].astype(str).str.strip().str.lower()
        codes_series = df_codes[target_col_codes].astype(str).str.strip().str.lower()
        valid_codes_set = set(codes_series)
        
        matched_mask = orders_series.isin(valid_codes_set)
        matched_df = df_orders[matched_mask].copy()
        unmatched_df = df_orders[~matched_mask]

        # --- B. FINANCIAL CALCULATIONS ---
        # Clean columns to ensure they are numbers
        matched_df['__clean_price'] = matched_df[col_price].apply(clean_currency)
        matched_df['__clean_discount'] = matched_df[col_discount].apply(clean_currency)

        # 1. Gross Income (Sum of Basket item price)
        total_gross = matched_df['__clean_price'].sum()

        # 2. Total Discount (Sum of مجموع مبلغ تخفیف)
        total_discount = matched_df['__clean_discount'].sum()

        # 3. Net Income (Price - Discount) <-- UPDATED HERE
        total_net = total_gross - total_discount

        # --- C. DISPLAY REPORT ---
        st.divider()
        st.subheader("📊 Financial Report (Matched Orders)")
        
        # Use columns for big metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Income (Basket Price)", f"{total_gross:,.0f}")
        m2.metric("Total Discount", f"{total_discount:,.0f}")
        m3.metric("Net Income (Price - Discount)", f"{total_net:,.0f}", delta_color="normal")

        st.info(f"Matched **{len(matched_df)}** orders out of **{len(df_orders)}** total.")

        # --- D. PREVIEW & DOWNLOAD ---
        st.write("### 👁️ Matched Orders Preview")
        st.dataframe(matched_df.head())
        
        # Drop helper columns before saving
        matched_df = matched_df.drop(columns=['__clean_price', '__clean_discount'])

        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
            matched_df.to_excel(writer, index=False, sheet_name="Matched")
            unmatched_df.to_excel(writer, index=False, sheet_name="Unmatched")
            
            # Add a Summary Sheet
            summary_df = pd.DataFrame({
                'Metric': ['Total Orders Processed', 'Matched Orders', 'Gross Income', 'Total Discount', 'Net Income'],
                'Value': [len(df_orders), len(matched_df), total_gross, total_discount, total_net]
            })
            summary_df.to_excel(writer, index=False, sheet_name="Summary")

        st.download_button(
            label="⬇️ Download Analysis (Excel)",
            data=output_buffer.getvalue(),
            file_name="financial_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )