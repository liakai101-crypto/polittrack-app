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

# 高級統一風格 CSS（解決重疊 + 美化）
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #e0e0e0; 
        padding: 25px 15px; 
        min-width: 300px !important; 
    }
    .sidebar-title { font-size: 1.4em; font-weight: 600; color: #0A84FF; margin-bottom: 20px; }
    .stButton > button { 
        background-color: #0A84FF; 
        color: white; 
        border-radius: 10px; 
        padding: 12px 24px; 
        font-weight: 500; 
        border: none; 
        transition: all 0.3s; 
        width: 100%; 
        margin-top: 15px; 
    }
    .stButton > button:hover { background-color: #0066cc; transform: translateY(-2px); }
    .stExpander { 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        background: white; 
        margin: 20px 0; 
    }
    .stExpander > div > div { padding: 15px; }
    .card { 
        background: white; 
        padding: 25px; 
        border-radius: 16px; 
        box-shadow: 0 6px 20px rgba(0,0,0,0.08); 
        margin-bottom: 25px; 
        text-align: center; 
    }
    .card h3 { color: #0A84FF; margin-bottom: 15px; font-size: 1.6em; }
    .card p { font-size: 1.4em; font-weight: 600; color: #333; margin: 0; }
    .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; padding: 30px 0; }
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

with st.sidebar.expander("進階篩選", expanded=False):
    search_donor_type = st.selectbox("捐款來源", ["全部", "企業", "個人", "團體"], key="sidebar_donor")
    search_year = st.slider("捐款年份範圍", 2020, 2025, (2020, 2025), key="sidebar_year")
    search_donation_range = st.slider("捐款金額範圍 (元)", 0, 100000000, (0, 100000000), key="sidebar_amount")
    search_area = st.selectbox("選區", ["全部"] + list(df['district'].unique()) if 'district' in df else ["全部"], key="sidebar_area")
    sort_by = st.selectbox("排序方式", ["無排序", "捐款金額降序", "財產增長率降序"], key="sidebar_sort")

st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

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
    total = filtered_df['donation_total'].sum() if 'donation_total' in filtered_df.columns else 0
    st.markdown(f'<div class="card"><h3>總捐款金額</h3><p>{total:,.0f} 元</p></div>', unsafe_allow_html=True)

with cols[1]:
    warnings = len(filtered_df[filtered_df['warning'] != ""])
    st.markdown(f'<div class="card"><h3>異常警示數</h3><p>{warnings}</p></div>', unsafe_allow_html=True)

with cols[2]:
    top_district = filtered_df.groupby('district')['donation_total'].sum().idxmax() if 'district' in filtered_df.columns and not filtered_df.empty else "無資料"
    st.markdown(f'<div class="card"><h3>最高捐款縣市</h3><p>{top_district}</p></div>', unsafe_allow_html=True)

with cols[3]:
    candidates = filtered_df['name'].nunique() if 'name' in filtered_df.columns else 0
    st.markdown(f'<div class="card"><h3>候選人數</h3><p>{candidates}</p></div>', unsafe_allow_html=True)

# ==================== 主內容分頁 ====================
tab1, tab2, tab3, tab4 = st.tabs(["資料查詢", "大額排行", "選區地圖", "完整資料"])

with tab1:
    st.header("查詢結果")
    st.dataframe(
        filtered_df.style.applymap(
            lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 10000000 else '',
            subset=['donation_total'] if 'donation_total' in filtered_df.columns else []
        ),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.header("大額捐款排行")
    top = filtered_df.sort_values('donation_amount', ascending=False).head(10) if 'donation_amount' in filtered_df.columns else pd.DataFrame()
    st.dataframe(top[['name', 'top_donor', 'donation_amount']])

with tab3:
    st.header("選區金流地圖")
    
    # 明確定義 map_data（避免 NameError）
    map_data = pd.DataFrame({
        'district': ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '新竹市', '嘉義市', '宜蘭縣', '新竹縣', '苗栗縣', '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '臺東縣', '花蓮縣', '澎湖縣', '金門縣', '連江縣'],
        'donation_total': [850000000, 650000000, 450000000, 550000000, 380000000, 480000000, 120000000, 180000000, 150000000, 200000000, 220000000, 190000000, 280000000, 160000000, 140000000, 130000000, 170000000, 110000000, 130000000, 80000000, 90000000, 50000000],
        'lat': [25.0330, 25.0120, 24.9934, 24.1477, 22.9999, 22.6273, 25.1337, 24.8138, 23.4807, 24.7503, 24.8270, 24.5643, 24.0510, 23.9601, 23.7089, 23.4811, 22.5519, 22.7554, 23.9743, 23.5655, 24.4360, 26.1500],
        'lon': [121.5654, 121.4589, 121.2999, 120.6736, 120.2270, 120.3133, 121.7425, 120.9686, 120.4491, 121.7470, 121.0129, 120.8269, 120.4818, 120.9716, 120.4313, 120.4491, 120.4918, 121.1500, 121.6167, 119.5655, 118.3200, 119.9500],
        'main_party': ['國民黨', '國民黨', '民進黨', '民進黨', '民進黨', '民進黨', '國民黨', '民眾黨', '民進黨', '民進黨', '國民黨', '國民黨', '民進黨', '民進黨', '民進黨', '民進黨', '民進黨', '民進黨', '國民黨', '無黨籍', '國民黨', '國民黨']
    })

    st.write("地圖資料筆數：", len(map_data))

    try:
        with open("taiwan_counties.geojson", "r", encoding="utf-8") as f:
            taiwan_geojson = json.load(f)
        st.write("GeoJSON 載入成功！開始繪製地圖...")
    except FileNotFoundError:
        st.error("找不到 taiwan_counties.geojson，請確認已上傳到 repo 根目錄")
        st.stop()

    fig_map = px.choropleth_mapbox(
        map_data,
        geojson=taiwan_geojson,
        locations='district',
        featureidkey='properties.name',
        color='donation_total',
        color_continuous_scale='Blues',
        hover_name='district',
        zoom=7.8,
        center={"lat": 23.58, "lon": 120.98},
        opacity=0.85,
        mapbox_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=700)
    st.plotly_chart(fig_map, use_container_width=True)

with tab4:
    st.header("完整資料庫")
    st.dataframe(df)

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後 commit 即可生效。")
