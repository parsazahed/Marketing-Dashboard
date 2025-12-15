import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="پنل ابزارهای جانبی",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Injection for Full RTL & Vazir Font
st.markdown("""
    <style>
        /* Import Vazirmatn Font */
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');

        /* Global RTL Direction */
        .stApp {
            direction: rtl;
            text-align: right;
        }

        /* Apply Font to Text Elements (But NOT Icons) */
        html, body, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .stButton, .stTextInput, .stSelectbox, .stSidebar {
            font-family: 'Vazirmatn', sans-serif !important;
        }

        /* Align Headers */
        h1, h2, h3, h4, h5, h6 {
            text-align: right !important;
        }

        /* Fix Column Alignment */
        div[data-testid="column"] {
            text-align: right !important;
            align-items: flex-start; 
        }

        /* Fix Sidebar Direction */
        section[data-testid="stSidebar"] {
            direction: rtl;
            text-align: right;
        }

        /* Fix Sidebar Navigation Links (Flip Icon & Text) */
        /* This makes the page icon appear on the Right side of the text */
        div[data-testid="stSidebarNav"] li div a {
             flex-direction: row-reverse; 
             justify-content: flex-end;
             text-align: right;
             padding-right: 20px; /* Add spacing if needed */
        }
        
        /* Fix Input Widgets direction */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            direction: rtl;
            text-align: right;
        }

    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🚀 ابزارهای داخلی جانبی")
st.markdown("---")

st.markdown("""
### سلام تیم جانبی! 👋
اینجا مرکز کنترل عملیات‌های جانبی است.  
برای شروع، ابزار مورد نظر خود را از **منوی کناری** انتخاب کنید.
""")

st.markdown("---")

# --- DASHBOARD GRID ---
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.header("🖼️ تصاویر محصولات")
        st.write("دانلود خودکار عکس‌ها از سایت، تغییر سایز و فشرده‌سازی گروهی.")
        st.info("👉 ابزار: **دانلود تصاویر**")

with col2:
    with st.container(border=True):
        st.header("🧹 پاکسازی داده")
        st.write("اصلاح شماره‌های موبایل، ادغام فایل‌های اکسل و حذف تکراری‌ها.")
        st.info("👉 ابزار: **تمیزکننده لیست**")

with col3:
    with st.container(border=True):
        st.header("🎫 عملیات‌ها")
        st.write("ساخت کدهای QR گروهی و سیستم تطبیق کدهای تخفیف اسنپ.")
        st.info("👉 ابزار: **سازنده QR / تطبیق کد**")

# --- SYSTEM STATUS ---
st.markdown("---")
st.caption("🟢 وضعیت سیستم: آنلاین | 🏢 داشبورد اتوماسیون جانبی")