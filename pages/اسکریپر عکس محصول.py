import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import zipfile
import concurrent.futures

st.set_page_config(page_title="Product Image Scraper", page_icon="🖼️", layout="centered")

st.title("High-Speed Image Scraper ⚡")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Output Settings")

# Dimensions & Format
target_w = st.sidebar.number_input("Target Width (px)", min_value=100, max_value=4000, value=512)
target_h = st.sidebar.number_input("Target Height (px)", min_value=100, max_value=4000, value=512)
img_format = st.sidebar.selectbox("Output Format", ["JPEG", "PNG"])
img_quality = st.sidebar.slider("JPEG Quality", 10, 100, 85) if img_format == "JPEG" else 100

st.sidebar.divider()

# SPEED SETTINGS
st.sidebar.header("🚀 Speed Control")
max_threads = st.sidebar.slider("Concurrent Downloads", 1, 20, 10, help="Higher = Faster, but risk of getting blocked.")

# --- HELPER FUNCTIONS ---
def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()

@st.cache_data(ttl=600)
def load_google_sheet(url):
    """Robust loader that handles GID and User-Agent blocking."""
    try:
        if "/d/" not in url:
            st.error("❌ Invalid URL. It must contain '/d/SHEET_ID/'.")
            return None
        sheet_id = url.split("/d/")[1].split("/")[0]
        gid = "0" 
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        # Pretend to be Chrome
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(export_url, headers=headers)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"❌ Error loading sheet: {e}")
        return None

def process_single_url(url, width, height, fmt, qual):
    """Worker function for threading."""
    try:
        # Pretend to be Chrome
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        # 1. Scrape
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 2. Find Image
        img_tag = soup.find("img", {"id": "main_product_image"})
        if not img_tag:
            return None, None, f"No image tag found"

        img_url = img_tag.get("data-zoom-image") or img_tag.get("src")
        if img_url.startswith("//"):
            img_url = "https:" + img_url

        # 3. Get Name
        alt_text = img_tag.get("alt", "product")
        filename = sanitize_filename(alt_text)
        ext = ".jpg" if fmt == "JPEG" else ".png"
        filename += ext

        # 4. Process Image
        img_data = requests.get(img_url, headers=headers, timeout=10)
        with Image.open(io.BytesIO(img_data.content)) as img:
            img = img.convert("RGB")
            img = img.resize((width, height), Image.LANCZOS)
            
            img_byte_arr = io.BytesIO()
            if fmt == "JPEG":
                img.save(img_byte_arr, format='JPEG', quality=qual)
            else:
                img.save(img_byte_arr, format='PNG')
                
            return filename, img_byte_arr.getvalue(), None
            
    except Exception as e:
        return None, None, str(e)

# --- MAIN INPUT SECTION ---
input_method = st.radio("Choose Input Method:", ["🔗 Single Link", "📂 Upload File", "☁️ Google Sheet"], horizontal=True)

df = None

# === METHOD 1: SINGLE LINK ===
if input_method == "🔗 Single Link":
    single_url = st.text_input("Enter Product URL:")
    if single_url and st.button("🚀 Process Link"):
        with st.spinner("Processing..."):
            fname, img_bytes, error = process_single_url(single_url, target_w, target_h, img_format, img_quality)
            if img_bytes:
                st.image(img_bytes, caption=fname, width=300)
                st.download_button(label="⬇️ Download", data=img_bytes, file_name=fname, mime=f"image/{img_format.lower()}")
            else:
                st.error(f"Error: {error}")

# === METHOD 2 & 3: BULK PROCESSING ===
else:
    if input_method == "📂 Upload File":
        uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file, header=1)
            st.success(f"Loaded {len(df)} rows.")

    elif input_method == "☁️ Google Sheet":
        sheet_url = st.text_input("Paste Google Sheet URL:")
        if sheet_url:
            df = load_google_sheet(sheet_url)
            if df is not None:
                st.success(f"Loaded {len(df)} rows.")

    if df is not None:
        # Select Column
        cols = df.columns.tolist()
        def_idx = cols.index("لینک محصول") if "لینک محصول" in cols else 0
        url_column = st.selectbox("Select URL Column:", cols, index=def_idx)

        if st.button(f"🚀 Start Fast Scraping ({max_threads} threads)"):
            urls = df[url_column].dropna().tolist()
            
            if not urls:
                st.warning("No URLs found.")
                st.stop()

            # --- PARALLEL EXECUTION ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            zip_buffer = io.BytesIO()
            
            results_data = [] # Store successful file data
            errors_log = []   # Store errors
            
            # Create a ThreadPool
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all tasks
                future_to_url = {executor.submit(process_single_url, url, target_w, target_h, img_format, img_quality): url for url in urls}
                
                completed_count = 0
                
                # Process as they finish
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    completed_count += 1
                    
                    try:
                        fname, img_bytes, error = future.result()
                        if img_bytes:
                            results_data.append((fname, img_bytes))
                        else:
                            errors_log.append(f"{url} -> {error}")
                    except Exception as exc:
                         errors_log.append(f"{url} -> {exc}")
                    
                    # Update UI
                    progress_pct = completed_count / len(urls)
                    progress_bar.progress(progress_pct)
                    status_text.text(f"Processed {completed_count}/{len(urls)}")

            # --- SAVE TO ZIP ---
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for fname, data in results_data:
                    # Handle duplicate names by prepending a number if needed, or rely on unique content
                    # Simple duplicate handler:
                    if fname in zf.namelist():
                        import uuid
                        fname = f"{uuid.uuid4().hex[:4]}_{fname}"
                    zf.writestr(f"images/{fname}", data)
                
                # Save error log if any
                if errors_log:
                    zf.writestr("errors.txt", "\n".join(errors_log))

            st.success(f"✅ Finished! {len(results_data)} images scraped. {len(errors_log)} errors.")
            
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_buffer.getvalue(),
                file_name="fast_images.zip",
                mime="application/zip"
            )