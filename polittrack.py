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

# Google Fonts + 統一高級風格 CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    h1, h2, h3 { color: #0A84FF; }
    h1 { font-size: 3.8em; font-weight: 700; margin-bottom: 0.3em; }
    .stButton > button { background-color: #0A84FF; color: white; border-radius: 10px; padding: 12px 24px; font-weight: 500; border: none; transition: all 0.3s; }
    .stButton > button:hover { background-color: #0066cc; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(10,132,255,0.3); }
    .stExpander { border: 1px solid #e0e0e0; border-radius: 12px; background: white; }
    .stDataFrame { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); margin-bottom: 25px; text-align: center; }
    .card h3 { color: #0A84FF; margin-bottom: 15px; font-size: 1.6em; }
    .card p { font-size: 1.4em; font-weight: 600; color: #333; margin: 0; }
    .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; padding: 30px; }
    .vision { background: linear-gradient(135deg, #f0f8ff, #e6f4ff); padding: 40px; border-radius: 20px; box-shadow: 0 8px 30px rgba(10,132,255,0.1); margin: 40px auto; max-width: 1100px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 登入功能
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.markdown("<div class='hero'><h1>NeoFormosa</h1><p class='slogan'>Taiwan’s Path to Global Integrity No.1</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='vision'><h2>登入以查看政治資金透明資料</h2></div>", unsafe_allow_html=True)
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

# ==================== 側邊欄篩選（精簡） ====================
st.sidebar.header("快速篩選")

search_name = st.sidebar.text_input("姓名或關鍵字")
search_party = st.sidebar.selectbox("黨籍", ["全部"] + list(df['party'].unique()) if 'party' in df else ["全部"])

with st.sidebar.expander("進階篩選"):
    search_donor_type = st.selectbox("捐款來源", ["全部", "企業", "個人", "團體"])
    search_year = st.slider("捐款年份", 2020, 2025, (2020, 2025))
    search_donation_range = st.slider("捐款金額範圍 (元)", 0, 100000000, (0, 100000000))
    search_area = st.selectbox("選區", ["全部"] + list(df['district'].unique()) if 'district' in df else ["全部"])
    sort_by = st.selectbox("排序", ["無排序", "捐款金額降序", "財產增長率降序"])

if st.sidebar.button("重置篩選"):
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

# ==================== 儀表板首頁 ====================
st.title("儀表板總覽")

dashboard_cols = st.columns(4)

with dashboard_cols[0]:
    st.markdown('<div class="card"><h3>總捐款金額</h3><p>{:,.0f} 元</p></div>'.format(filtered_df['donation_total'].sum()), unsafe_allow_html=True)

with dashboard_cols[1]:
    st.markdown('<div class="card"><h3>異常警示數</h3><p>{}</p></div>'.format(len(filtered_df[filtered_df['warning'] != ""])), unsafe_allow_html=True)

with dashboard_cols[2]:
    st.markdown('<div class="card"><h3>最高捐款縣市</h3><p>{}</p></div>'.format(filtered_df.groupby('district')['donation_total'].sum().idxmax()), unsafe_allow_html=True)

with dashboard_cols[3]:
    st.markdown('<div class="card"><h3>候選人數</h3><p>{}</p></div>'.format(filtered_df['name'].nunique()), unsafe_allow_html=True)

# ==================== 主內容分頁 ====================
tab1, tab2, tab3, tab4 = st.tabs(["資料查詢", "大額捐款排行", "選區金流地圖", "完整資料庫"])

with tab1:
    st.header("查詢結果")
    st.dataframe(
        filtered_df.style.applymap(
            lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 10000000 else '',
            subset=['donation_total']
        ),
        use_container_width=True,
        column_config={
            "donation_total": st.column_config.NumberColumn("捐款總額", format="%d 元"),
            "warning": st.column_config.TextColumn("警示"),
        },
        hide_index=True
    )

    st.subheader("財產趨勢圖")
    fig_trend = px.line(filtered_df, x='name', y=['assets_2024', 'assets_2025'], title='財產變化')
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.header("大額捐款者排行榜")
    top_donors = filtered_df.sort_values('donation_amount', ascending=False).head(15)
    st.dataframe(top_donors[['name', 'top_donor', 'donation_amount']])
    fig_rank = px.bar(top_donors, x='top_donor', y='donation_amount', color='name')
    st.plotly_chart(fig_rank, use_container_width=True)

with tab3:
    st.header("選區金流地圖")
    try:
        with open("taiwan_counties.geojson", "r", encoding="utf-8") as f:
            taiwan_geojson = json.load(f)
    except FileNotFoundError:
        st.error("找不到 taiwan_counties.geojson")
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
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=700)
    st.plotly_chart(fig_map, use_container_width=True)

with tab4:
    st.header("完整資料庫")
    st.dataframe(df)

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後重新 commit 即可生效。")
