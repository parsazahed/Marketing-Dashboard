import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Mass SMS Cleaner", page_icon="🧹", layout="centered")

st.title("Mass SMS Cleaner & Merger 🧹")
st.write("Upload multiple Excel files. I will merge them, clean the numbers, and remove duplicates across the entire list.")

# --- SIDEBAR: CLEANING RULES ---
st.sidebar.header("⚙️ Cleaning Rules")

st.sidebar.caption("1. Formatting")
opt_convert_digits = st.sidebar.checkbox("Convert Farsi/Arabic digits (۱۲۳ -> 123)", value=True)
opt_remove_nondigits = st.sidebar.checkbox("Remove non-digits ( - / spaces )", value=True)
opt_fix_prefix = st.sidebar.checkbox("Fix Prefix (98912... -> 0912...)", value=True)

st.sidebar.caption("2. Filtering")
opt_remove_dupes = st.sidebar.checkbox("Remove Duplicate Numbers (Global)", value=True)
opt_filter_length = st.sidebar.checkbox("Keep ONLY 11-digit numbers", value=True)
opt_filter_mobile = st.sidebar.checkbox("Keep ONLY starting with '09'", value=True)

# --- HELPER FUNCTIONS ---
def clean_single_number(number):
    """Applies cleaning logic based on sidebar selections."""
    if pd.isna(number) or str(number).strip() == "":
        return None
    
    number = str(number).strip()

    # 1. Translation (Farsi/Arabic -> English)
    if opt_convert_digits:
        farsi = '۰۱۲۳۴۵۶۷۸۹'
        arabic = '٠١٢٣٤٥٦٧٨٩'
        english = '0123456789'
        mapping = str.maketrans(farsi + arabic, english * 2)
        number = number.translate(mapping)

    # 2. Handle Prefixes (do +98 / 0098 BEFORE stripping non-digits)
    if opt_fix_prefix:
        if number.startswith('+98'):
            number = '0' + number[3:]
        elif number.startswith('0098'):
            number = '0' + number[4:]

    # 3. Remove Non-Digits
    if opt_remove_nondigits:
        number = re.sub(r'\D', '', number)

    # 4. Handle Prefixes (after stripping non-digits)
    if opt_fix_prefix:
        if number.startswith('98') and len(number) > 10:
            number = '0' + number[2:]
        elif number.startswith('9') and len(number) == 10:
            number = '0' + number

    # --- VALIDATION CHECKS ---
    if opt_filter_length and len(number) != 11:
        return None

    if opt_filter_mobile and not number.startswith("09"):
        return None

    return number

def read_file(uploaded_file):
    """Reads CSV or Excel and returns a DataFrame."""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file, dtype=str)
        else:
            return pd.read_excel(uploaded_file, dtype=str)
    except Exception as e:
        st.warning(f"Skipping {uploaded_file.name}: {e}")
        return None

# --- MAIN APP LOGIC ---

uploaded_files = st.file_uploader(
    "Upload Excel/CSV Files (You can select multiple)", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📂 {len(uploaded_files)} files selected.")
    
    if st.button("🚀 Merge & Clean All"):
        all_dfs = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step A: Read and Merge
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Reading file {i+1}/{len(uploaded_files)}: {file.name}")
            df_temp = read_file(file)
            if df_temp is not None:
                df_temp['_source_file'] = file.name
                all_dfs.append(df_temp)
            progress_bar.progress((i + 1) / (len(uploaded_files) * 2))

        if not all_dfs:
            st.error("No valid data found.")
            st.stop()

        status_text.text("Merging files...")
        full_df = pd.concat(all_dfs, ignore_index=True)
        initial_count = len(full_df)

        # Step B: Identify Column
        cols = full_df.columns.tolist()
        target_col = None
        possible_names = ['mobile', 'phone', 'cell', 'شماره', 'tel', 'mob']
        for col in cols:
            if any(x in str(col).lower() for x in possible_names):
                target_col = col
                break
        
        if not target_col:
            target_col = cols[0]

        # Step C: Cleaning
        status_text.text("Cleaning numbers...")
        full_df['Cleaned_Mobile'] = full_df[target_col].apply(clean_single_number)
        
        # Step D: Filter & Deduplicate
        valid_df = full_df.dropna(subset=['Cleaned_Mobile'])
        
        final_df = valid_df.copy()
        dupe_count = 0
        
        if opt_remove_dupes:
            status_text.text("Removing global duplicates...")
            before_dedup = len(final_df)
            final_df = final_df.drop_duplicates(subset=['Cleaned_Mobile'])
            dupe_count = before_dedup - len(final_df)

        progress_bar.progress(1.0)
        status_text.text("Done!")
        
        # --- RESULTS & PREVIEW ---
        st.divider()
        st.subheader("📊 Results & Preview")
        
        # 1. Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Rows", initial_count)
        c2.metric("Duplicates Removed", dupe_count)
        c3.metric("Final Valid List", len(final_df))
        
        # 2. Preview Table
        st.write("### 👁️ Preview of Final Data")
        st.write("Checking the first 5 rows to ensure formatting is correct:")
        
        # We show the Source File, Original Number, and Cleaned Number for comparison
        preview_cols = ['_source_file', target_col, 'Cleaned_Mobile']
        # Add any other cols if they exist but ensure we don't crash
        preview_cols = [c for c in preview_cols if c in final_df.columns]
        
        st.dataframe(final_df[preview_cols].head(10), use_container_width=True)

        # 3. Download
        output_buffer = io.BytesIO()
        
        if len(final_df) > 100000:
            st.warning("⚠️ File is large (>100k rows), downloading as CSV.")
            final_df.to_csv(output_buffer, index=False)
            mime_type = "text/csv"
            ext = "csv"
        else:
            with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
            
        st.download_button(
            label=f"⬇️ Download Final List ({ext})",
            data=output_buffer.getvalue(),
            file_name=f"merged_cleaned_list.{ext}",
            mime=mime_type,
            type="primary"
        )