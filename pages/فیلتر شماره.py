import streamlit as st
import pandas as pd
import io
import re

# --- Helper Function: Smart Normalization ---
def standardize_iranian_number(val):
    """
    1. Converts value to string.
    2. Removes all non-numeric characters ( +, -, spaces).
    3. Extracts the last 10 digits.
       Ex: '+98 912 606 0760' -> '9126060760'
       Ex: '09126060760'      -> '9126060760'
    """
    # Convert to string and strip whitespace
    s = str(val).strip()
    
    # Remove anything that is NOT a digit (0-9)
    # This handles +98, dashes, parenthesis, etc.
    digits_only = re.sub(r'\D', '', s)
    
    # Logic: Iranian mobile numbers rely on the last 10 digits to be unique.
    # (e.g. 912xxxxxxx). 
    if len(digits_only) >= 10:
        return digits_only[-10:]
    else:
        # If the number is too short (bad data), return it as is digits-only
        return digits_only

# --- Main App Layout ---
st.set_page_config(page_title="Smart Row Remover", layout="centered")

st.title("🇮🇷 Smart Phone Number Filter")
st.markdown("""
This tool removes rows from your **Main File** based on numbers in a **Filter File**.
**Smart Feature:** It automatically handles formats like `0912...`, `+98912...`, or `98912...`.
""")

st.markdown("---")

# 1. File Uploaders
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Main File (To Clean)")
    file1 = st.file_uploader("Upload Main Excel/CSV", type=["xlsx", "xls", "csv"], key="f1")

with col2:
    st.subheader("2. Filter File (Blocklist)")
    file2 = st.file_uploader("Upload Filter Excel/CSV", type=["xlsx", "xls", "csv"], key="f2")

# 2. Processing
if file1 and file2:
    # Load data
    try:
        df_main = pd.read_csv(file1) if file1.name.endswith('.csv') else pd.read_excel(file1)
        df_filter = pd.read_csv(file2) if file2.name.endswith('.csv') else pd.read_excel(file2)
    except Exception as e:
        st.error(f"Error reading files: {e}")
        st.stop()

    st.markdown("---")
    
    # 3. Column Selection
    c1, c2 = st.columns(2)
    with c1:
        main_col = st.selectbox("Column in Main File:", df_main.columns)
    with c2:
        filter_col = st.selectbox("Column in Filter File:", df_filter.columns)

    # 4. Settings
    st.caption("Settings")
    use_smart_match = st.checkbox("✅ Enable Smart Matching (Recommended)", value=True, 
                                  help="Matches numbers regardless of 0, 98, or +98 formatting.")

    # 5. Action
    if st.button("Run Cleaner"):
        with st.spinner("Normalizing and comparing numbers..."):
            
            # A. Prepare the Filter List
            if use_smart_match:
                # Create a set of "Standardized" numbers from the filter file
                # We use a set for O(1) lookup speed (very fast)
                filter_set = set(df_filter[filter_col].apply(standardize_iranian_number))
                
                # Create a temporary column in Main DF for comparison
                temp_comparison_col = df_main[main_col].apply(standardize_iranian_number)
                
                # Logic: Keep row if the standardized version is NOT in the filter set
                mask = ~temp_comparison_col.isin(filter_set)
                
            else:
                # Exact string matching (old way)
                filter_set = set(df_filter[filter_col].astype(str).str.strip())
                mask = ~df_main[main_col].astype(str).str.strip().isin(filter_set)

            # Apply the mask
            df_cleaned = df_main[mask]

            # Calculate stats
            total_rows = len(df_main)
            removed = total_rows - len(df_cleaned)
            remaining = len(df_cleaned)

            # Display Output
            st.success(f"Done! Removed {removed} rows.")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Original", total_rows)
            m2.metric("Removed", removed, delta_color="inverse")
            m3.metric("Result", remaining)

            # Preview
            st.write("### Preview Result")
            st.dataframe(df_cleaned.head())

            # Download
            buffer = io.BytesIO()
            # Default to Excel, but could be CSV
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_cleaned.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Cleaned File",
                data=buffer,
                file_name="cleaned_numbers.xlsx",
                mime="application/vnd.ms-excel"
            )

elif not file1 and not file2:
    st.info("Waiting for files...")