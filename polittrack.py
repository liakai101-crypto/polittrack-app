import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
import datetime
from fpdf import FPDF

# ==================== 頁面設定與美化 ====================
st.set_page_config(
    page_title="NeoFormosa - 台灣政治透明平台",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 高級統一風格 CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; padding: 20px 15px; }
    h1, h2, h3 { color: #0A84FF; }
    .stButton > button { background-color: #0A84FF; color: white; border-radius: 10px; padding: 12px 24px; font-weight: 500; border: none; transition: all 0.3s; width: 100%; margin-top: 15px; }
    .stButton > button:hover { background-color: #0066cc; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(10,132,255,0.3); }
    .stExpander { border: 1px solid #e0e0e0; border-radius: 12px; background: white; margin-top: 20px; }
    .stExpander > div > div { padding: 15px; }
    .sidebar-title { font-size: 1.3em; font-weight: 600; color: #0A84FF; margin-bottom: 15px; }
    .sidebar-divider { border-top: 1px solid #e0e0e0; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# 登入功能
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.markdown("<div style='text-align:center; padding:100px 20px;'><h1>NeoFormosa</h1><p>Taiwan’s Path to Global Integrity No.1</p></div>", unsafe_allow_html=True)
    username = st.text_input("使用者名稱")
    password = st.text_input("密碼", type="password")
    if st.button("登入", use_container_width=True):
        if username == "admin" and password == "poli2026":
            st.session_state.logged_in = True
            st.success("登入成功！")
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")

if not st.session_state.logged_in:
    login()
    st.stop()

# ==================== 讀取資料 ====================
with st.spinner("載入資料中..."):
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv("polittrack_data.csv", encoding='utf-8-sig')
            return df
        except FileNotFoundError:
            st.error("找不到 polittrack_data.csv")
            return pd.DataFrame()

    df = load_data()

last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
st.sidebar.success(f"資料最後更新：{last_update}")

# ==================== 側邊欄 - 極簡版 ====================
st.sidebar.markdown('<div class="sidebar-title">快速篩選</div>', unsafe_allow_html=True)

search_name = st.sidebar.text_input("姓名或關鍵字", key="sidebar_name")
search_party = st.sidebar.selectbox("黨籍", ["全部"] + list(df['party'].unique()) if 'party' in df else ["全部"], key="sidebar_party")

with st.sidebar.expander("進階篩選"):
    search_donor_type = st.selectbox("捐款來源", ["全部", "企業", "個人", "團體"], key="sidebar_donor")
    search_year = st.slider("捐款年份範圍", 2020, 2025, (2020, 2025), key="sidebar_year")
    search_donation_range = st.slider("捐款金額範圍 (元)", 0, 100000000, (0, 100000000), key="sidebar_amount")
    search_area = st.selectbox("選區", ["全部"] + list(df['district'].unique()) if 'district' in df else ["全部"], key="sidebar_area")
    sort_by = st.selectbox("排序方式", ["無排序", "捐款金額降序", "財產增長率降序"], key="sidebar_sort")

if st.sidebar.button("重置篩選", use_container_width=True):
    st.rerun()

# 過濾資料
filtered_df = df.copy()
if search_name:
    query = search_name.lower()
    filtered_df = filtered_df[
        filtered_df['name'].str.lower().str.contains(query, na=False) |
        filtered_df.get('top_donor', pd.Series()).str.lower().str.contains(query, na=False)
    ]
if search_party != "全部":
    filtered_df = filtered_df[filtered_df['party'] == search_party]
if search_donor_type != "全部":
    filtered_df = filtered_df[filtered_df['donor_type'] == search_donor_type]
filtered_df = filtered_df[(filtered_df['donation_year'] >= search_year[0]) & (filtered_df['donation_year'] <= search_year[1])]
filtered_df = filtered_df[(filtered_df['donation_total'] >= search_donation_range[0]) & (filtered_df['donation_total'] <= search_donation_range[1])]
if search_area != "全部":
    filtered_df = filtered_df[filtered_df['district'] == search_area]

if sort_by == "捐款金額降序":
    filtered_df = filtered_df.sort_values('donation_total', ascending=False)
elif sort_by == "財產增長率降序":
    filtered_df['growth_rate'] = (filtered_df['assets_2025'] - filtered_df['assets_2024']) / filtered_df['assets_2024'] * 100
    filtered_df = filtered_df.sort_values('growth_rate', ascending=False)

# 防呆：確保 warning 欄位存在
filtered_df['warning'] = filtered_df.apply(lambda row: "⚠️ 異常" if row.get('donation_amount', 0) > 10000000 else "", axis=1)

# ==================== 儀表板總覽 ====================
st.title("儀表板總覽")

cols = st.columns(4)
with cols[0]:
    total = filtered_df['donation_total'].sum() if 'donation_total' in filtered_df else 0
    st.markdown(f'<div class="card"><h3>總捐款金額</h3><p>{total:,.0f} 元</p></div>', unsafe_allow_html=True)

with cols[1]:
    warnings = len(filtered_df[filtered_df['warning'] != ""])
    st.markdown(f'<div class="card"><h3>異常警示</h3><p>{warnings}</p></div>', unsafe_allow_html=True)

with cols[2]:
    top_district = filtered_df.groupby('district')['donation_total'].sum().idxmax() if not filtered_df.empty else "無"
    st.markdown(f'<div class="card"><h3>最高捐款縣市</h3><p>{top_district}</p></div>', unsafe_allow_html=True)

with cols[3]:
    candidates = filtered_df['name'].nunique()
    st.markdown(f'<div class="card"><h3>候選人數</h3><p>{candidates}</p></div>', unsafe_allow_html=True)

# ==================== 主內容分頁 ====================
tab1, tab2, tab3, tab4 = st.tabs(["資料查詢", "大額排行", "選區地圖", "完整資料"])

with tab1:
    st.header("查詢結果")
    st.dataframe(
        filtered_df.style.applymap(
            lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 10000000 else '',
            subset=['donation_total'] if 'donation_total' in filtered_df else []
        ),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.header("大額捐款排行")
    top = filtered_df.sort_values('donation_amount', ascending=False).head(10)
    st.dataframe(top[['name', 'top_donor', 'donation_amount']])

with tab3:
    st.header("選區金流地圖")
    # 這裡放你的地圖程式碼（已修正 len(map_data)）
    st.write("地圖資料筆數：", len(map_data))
    # ... 你的地圖程式碼 ...

with tab4:
    st.header("完整資料庫")
    st.dataframe(df)

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後 commit 即可生效。")
