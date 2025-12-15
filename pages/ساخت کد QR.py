import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io
import zipfile
from urllib.parse import urlparse
import requests

st.set_page_config(page_title="QR Code Generator", page_icon="🔗", layout="centered")

st.title("Universal QR Code Generator 🔗")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Design Settings")

# Color Settings
qr_color = st.sidebar.color_picker("QR Data Color", "#000000") 
bg_choice = st.sidebar.radio("Background Style", ["Transparent", "Solid Color"])

if bg_choice == "Solid Color":
    bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF") 
else:
    bg_color = None # Transparent

# Size Settings
box_size = st.sidebar.slider("Size (Box Pixel)", 10, 50, 20) 
border_size = st.sidebar.slider("Border (Quiet Zone)", 0, 10, 4)

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

def generate_qr(link, fill_hex, back_hex_or_none, box, border):
    """Generates a PIL Image of the QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box,
        border=border,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    
    datas = img.getdata()
    new_data = []
    
    # Convert hex to RGB tuple
    fill_rgb = tuple(int(fill_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    if back_hex_or_none:
        back_rgb = tuple(int(back_hex_or_none.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    else:
        back_rgb = (0, 0, 0, 0)

    for item in datas:
        if item[0] == 0: 
            new_data.append(fill_rgb + (255,)) 
        else:
            if back_hex_or_none:
                new_data.append(back_rgb + (255,))
            else:
                new_data.append((255, 255, 255, 0)) 

    img.putdata(new_data)
    return img

def get_slug(url):
    """Extracts a clean filename from the URL."""
    try:
        parsed = urlparse(url)
        slug = parsed.path.rsplit("/", 1)[-1]
        if not slug:
            return "qr_code"
        return slug
    except:
        return "qr_code"

# --- MAIN INPUT SECTION ---
input_method = st.radio("Choose Input Method:", ["🔗 Single Link", "📂 Upload File", "☁️ Google Sheet"], horizontal=True)

df = None
single_link = None

# === METHOD 1: SINGLE LINK ===
if input_method == "🔗 Single Link":
    single_link = st.text_input("Enter URL here:", "https://janebi.com")
    
    if single_link:
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
        
        # Preview One
        if not df.empty:
            preview_url = str(df[link_column].iloc[0])
            st.caption(f"Previewing style using first row: {preview_url}")
            preview_img = generate_qr(preview_url, qr_color, bg_color, box_size, border_size)
            st.image(preview_img, width=150)

        # Generate Button
        if st.button("🚀 Generate All QR Codes"):
            links = df[link_column].dropna().tolist()
            
            progress_bar = st.progress(0)
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for i, raw_link in enumerate(links):
                    link = str(raw_link).strip()
                    if not link: continue
                    
                    if not link.startswith(("http://", "https://")):
                        link = "https://" + link

                    img = generate_qr(link, qr_color, bg_color, box_size, border_size)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    
                    filename = f"{get_slug(link)}.png"
                    if filename in zf.namelist():
                        filename = f"{get_slug(link)}_{i}.png"
                    
                    zf.writestr(filename, img_byte_arr.getvalue())
                    progress_bar.progress((i + 1) / len(links))
            
            st.success("🎉 Done!")
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_buffer.getvalue(),
                file_name="qr_codes_bulk.zip",
                mime="application/zip"
            )