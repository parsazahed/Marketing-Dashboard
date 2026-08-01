import streamlit as st
import pandas as pd
import io
import zipfile
import requests

from qr_utils import contrast_ratio, generate_qr, get_slug, normalize_link

st.set_page_config(page_title="QR Code Generator", page_icon="🔗", layout="centered")

st.title("Universal QR Code Generator 🔗")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Design Settings")

# Color Settings
qr_color = st.sidebar.color_picker("QR Data Color", "#000000") 
bg_choice = st.sidebar.radio("Background Style", ["Solid Color", "Transparent"])

if bg_choice == "Solid Color":
    bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF") 
else:
    bg_color = None # Transparent

# Size Settings
box_size = st.sidebar.slider("Size (Box Pixel)", 10, 50, 20)
border_size = st.sidebar.slider("Border (Quiet Zone)", 4, 10, 4)

if bg_color and contrast_ratio(qr_color, bg_color) < 4.5:
    st.sidebar.warning("⚠️ Low color contrast may make this QR code hard to scan.")
elif bg_color is None:
    st.sidebar.warning("⚠️ Transparent QR codes need a light, plain background when used.")

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=600)  # Caches data for 10 mins so it's faster
def load_google_sheet(url):
    """Robust loader that handles GID and User-Agent blocking."""
    try:
        # 1. Extract Sheet ID
        if "/d/" not in url:
            st.error("❌ Invalid URL. It must contain '/d/SHEET_ID/'.")
            return None
            
        sheet_id = url.split("/d/")[1].split("/")[0]

        # 2. Extract Tab ID (gid) - Important for specific tabs!
        gid = "0" 
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]

        # 3. Construct Export URL
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        # 4. Pretend to be a Browser (Crucial Step!)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(export_url, headers=headers)
        response.raise_for_status() # Check for 403/404 errors

        # 5. Load into Pandas
        df = pd.read_csv(io.StringIO(response.text))
        return df

    except Exception as e:
        st.error(f"❌ Error loading sheet: {e}")
        st.warning("👉 Tip: Make sure the sheet is 'Anyone with the link' > 'Viewer'.")
        return None

# --- MAIN INPUT SECTION ---
input_method = st.radio("Choose Input Method:", ["🔗 Single Link", "📂 Upload File", "☁️ Google Sheet"], horizontal=True)

df = None
single_link = None

# === METHOD 1: SINGLE LINK ===
if input_method == "🔗 Single Link":
    single_link = st.text_input("Enter URL here:", "https://janebi.com")
    
    if single_link.strip():
        single_link = normalize_link(single_link)
        st.subheader("Preview & Download")
        img = generate_qr(single_link, qr_color, bg_color, box_size, border_size)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(img, caption="QR Preview", width=250)
        with col2:
            # Prepare download
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            
            st.download_button(
                label="⬇️ Download This QR Code",
                data=img_byte_arr.getvalue(),
                file_name=f"qr_{get_slug(single_link)}.png",
                mime="image/png"
            )

# === METHOD 2 & 3: BULK PROCESSING ===
else:
    # Load Data Frame based on selection
    if input_method == "📂 Upload File":
        uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    elif input_method == "☁️ Google Sheet":
        sheet_url = st.text_input("Paste Google Sheet URL (Must be 'Anyone with link'):")
        if sheet_url:
            df = load_google_sheet(sheet_url)
            if df is not None:
                st.success(f"✅ Loaded Google Sheet with {len(df)} rows.")
            else:
                st.error("❌ Could not load sheet.")

    if df is not None and len(df.columns) == 0:
        st.warning("The uploaded source does not contain any columns.")
        df = None

    # Process Data Frame if Loaded
    if df is not None:
        st.divider()
        st.subheader("Bulk Generation")
        
        # Column Selection
        col_options = df.columns.tolist()
        default_index = 0
        if "link" in col_options:
            default_index = col_options.index("link")
            
        link_column = st.selectbox("Select Column with Links:", col_options, index=default_index)

        valid_links = [
            normalize_link(value)
            for value in df[link_column].dropna().tolist()
            if str(value).strip()
        ]

        # Preview One
        if valid_links:
            preview_url = valid_links[0]
            st.caption(f"Previewing style using first row: {preview_url}")
            preview_img = generate_qr(preview_url, qr_color, bg_color, box_size, border_size)
            st.image(preview_img, width=150)
        else:
            st.warning("The selected column does not contain any links.")

        # Generate Button
        if st.button("🚀 Generate All QR Codes", disabled=not valid_links):
            progress_bar = st.progress(0)
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for i, link in enumerate(valid_links):
                    img = generate_qr(link, qr_color, bg_color, box_size, border_size)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    
                    filename = f"{get_slug(link)}.png"
                    if filename in zf.namelist():
                        filename = f"{get_slug(link)}_{i}.png"
                    
                    zf.writestr(filename, img_byte_arr.getvalue())
                    progress_bar.progress((i + 1) / len(valid_links))
            
            st.success("🎉 Done!")
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_buffer.getvalue(),
                file_name="qr_codes_bulk.zip",
                mime="application/zip"
            )
