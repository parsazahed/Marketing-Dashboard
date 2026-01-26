import streamlit as st
import pandas as pd
import io
import re
import csv

# --- Helper Function: Smart Normalization ---
def standardize_iranian_number(val):
    """
    1. Converts value to string.
    2. Removes all non-numeric characters (+, -, spaces).
    3. Extracts the last 10 digits.
       Ex: '+98 912 606 0760' -> '9126060760'
       Ex: '09126060760'      -> '9126060760'
    """
    s = str(val).strip()
    digits_only = re.sub(r'\D', '', s)
    
    if len(digits_only) >= 10:
        return digits_only[-10:]
    else:
        return digits_only

# --- Helper: Load File ---
def load_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            # خواندن چند خط اول برای تشخیص جداکننده
            content = uploaded_file.read(2048).decode('utf-8')
            uploaded_file.seek(0)
            
            dialect = csv.Sniffer().sniff(content)
            return pd.read_csv(uploaded_file, sep=dialect.delimiter)
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        # در صورت شکست Sniffer، به حالت پیش‌فرض ویرگول برمی‌گردیم
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=',')
        except:
            st.error(f"Error loading {uploaded_file.name}: {e}")
            return None
# --- Main App Layout ---

st.set_page_config(page_title="Multi-File Smart Cleaner", layout="wide")

st.title("🇮🇷 Multi-File Smart Phone Filter")
st.markdown("""
Upload one **Main File** and **Multiple Filter Files**. 
The app will combine all numbers from the filter files and remove them from the Main File.
""")

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Main File (To Clean)")
    main_file = st.file_uploader("Upload Main File", type=["xlsx", "xls", "csv"], key="main")

with col2:
    st.subheader("2. Filter Files (Blocklist)")
    # accept_multiple_files=True allows selecting multiple files at once
    filter_files = st.file_uploader("Upload one or more files", type=["xlsx", "xls", "csv"], 
                                    accept_multiple_files=True, key="filters")

# --- Processing Logic ---
if main_file and filter_files:
    
    # 1. Load Main File
    df_main = load_file(main_file)
    
    # 2. Load First Filter File (to get column names)
    # We read the first file just to populate the Dropdown menu
    first_filter_df = load_file(filter_files[0])

    if df_main is not None and first_filter_df is not None:
        st.markdown("---")
        st.subheader("3. Column Mapping")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            main_col = st.selectbox("Select ID Column in Main File:", df_main.columns)
            
        with c2:
            # We assume all filter files have the same column name for the phone number
            filter_col = st.selectbox("Select ID Column in Filter Files:", first_filter_df.columns,
                                      help="Ensure all your filter files have this column header!")
        
        with c3:
            st.write("") # Spacer
            st.write("") # Spacer
            use_smart = st.checkbox("✅ Smart Matching", value=True, 
                                    help="Ignores +98, 0, spaces, etc.")

        st.markdown("---")

        if st.button("🚀 Run Multi-File Cleaning", type="primary"):
            
            # --- Step A: Build the Master Blocklist ---
            master_blocklist = set()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Loop through all uploaded filter files
            for i, f_file in enumerate(filter_files):
                status_text.text(f"Processing filter file: {f_file.name}...")
                
                df_temp = load_file(f_file)
                
                if df_temp is not None:
                    # Check if the selected column exists in this file
                    if filter_col in df_temp.columns:
                        # Extract numbers
                        raw_numbers = df_temp[filter_col].dropna().astype(str)
                        
                        if use_smart:
                            # Apply standardization to this file's numbers
                            clean_nums = raw_numbers.apply(standardize_iranian_number)
                            master_blocklist.update(clean_nums)
                        else:
                            master_blocklist.update(raw_numbers.str.strip())
                    else:
                        st.warning(f"⚠️ Column '{filter_col}' not found in {f_file.name}. Skipping this file.")
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(filter_files))

            status_text.text("Applying filter to Main File...")
            
            # --- Step B: Clean the Main File ---
            if use_smart:
                main_vals_normalized = df_main[main_col].apply(standardize_iranian_number)
                mask = ~main_vals_normalized.isin(master_blocklist)
            else:
                mask = ~df_main[main_col].astype(str).str.strip().isin(master_blocklist)
            
            df_cleaned = df_main[mask]
            
            # Stats
            original_count = len(df_main)
            removed_count = original_count - len(df_cleaned)
            final_count = len(df_cleaned)
            
            progress_bar.empty()
            status_text.empty()

            # --- Results ---
            st.success("Processing Complete!")
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Total Rows in Main File", original_count)
            kpi2.metric("Total Rows Removed", removed_count, delta_color="inverse")
            kpi3.metric("Rows Remaining", final_count)
            
            with st.expander("See Cleaned Data Preview"):
                st.dataframe(df_cleaned.head(20))
            
            # --- Download ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_cleaned.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Result (Excel)",
                data=buffer,
                file_name="cleaned_master_list.xlsx",
                mime="application/vnd.ms-excel"
            )

elif not main_file or not filter_files:
    st.info("👋 Please upload your files to begin.")