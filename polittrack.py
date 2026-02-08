import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
import datetime
from fpdf import FPDF

# ==================== 頁面設定 ====================
st.set_page_config(
    page_title="Taiwan PoliTrack - 政治透明平台",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Flag_of_the_Republic_of_China.svg/32px-Flag_of_the_Republic_of_China.svg.png",
    layout="wide"
)

# ==================== 深色科技風格 CSS ====================
st.markdown("""
<style>
    /* 整體背景 - 深黑藍漸層 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #e0e0ff;
    }

    /* 側邊欄 - 半透明黑 */
    section[data-testid="stSidebar"] > div:first-child {
        background: rgba(20, 20, 40, 0.85);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 255, 255, 0.15);
    }

    /* 標題與文字 */
    h1, h2, h3 {
        color: #00f0ff !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }

    p, div, span, label {
        color: #d0d0ff !important;
    }

    /* 按鈕 - 藍綠發光 */
    .stButton > button {
        background: linear-gradient(45deg, #00b4d8, #48cae4);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        box-shadow: 0 0 15px rgba(0, 180, 216, 0.6);
        transition: all 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.9);
        transform: translateY(-2px);
    }

    /* 輸入框與選擇器 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(30, 30, 60, 0.8);
        color: #e0e0ff;
        border: 1px solid #00f0ff44;
        border-radius: 6px;
    }

    /* 分頁標籤 */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 20, 40, 0.7);
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0a0ff;
    }
    .stTabs [aria-selected="true"] {
        color: #00f0ff !important;
        background: rgba(0, 240, 255, 0.15);
    }

    /* 資料表格 */
    .stDataFrame {
        background: rgba(30, 30, 60, 0.6);
        border: 1px solid #00f0ff33;
        border-radius: 8px;
    }

    /* 地圖容器 */
    .stPlotlyChart {
        background: rgba(10, 10, 30, 0.7);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# 加 logo (保持原樣或改成發光版)
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Flag_of_the_Republic_of_China.svg/320px-Flag_of_the_Republic_of_China.svg.png", width=80)

st.title('Taiwan PoliTrack - 台灣政治透明平台')

st.markdown("""
**平台中立聲明**  
本平台僅呈現政府公開資料，不添加任何主觀評論、不做立場傾向、不涉及政治宣傳。  
所有資料來源自監察院、立法院等官方公開平台，使用者可自行驗證。  
如有錯誤，請聯絡我們（未來加回報表單）。  
本平台目標：促進公民資訊透明與參與。
""")

col1, col2 = st.columns(2)
with col1:
    st.markdown("[監察院政治獻金公開平台](https://ardata.cy.gov.tw)")
with col2:
    st.markdown("[立法院開放資料平台](https://data.ly.gov.tw)")

# 登入功能 (保持原樣)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Taiwan PoliTrack 登入")
    username = st.text_input("使用者名稱")
    password = st.text_input("密碼", type="password")
    if st.button("登入"):
        if username == "admin" and password == "poli2026":
            st.session_state.logged_in = True
            st.success("登入成功！")
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")

if not st.session_state.logged_in:
    login()
    st.stop()

# 讀取資料與其他功能保持原樣（略過重複部分，節省空間）
# ... (把你原本的 load_data、篩選、地圖計算邏輯全部貼回來)

# 地圖部分範例（可替換成你最新的 tab3）
with tab3:
    st.header('選區金流地圖（真實資料版）')
    
    # 你的 real_map_data 計算邏輯...
    # ... (保持你最新的真實資料整合部分)

    fig_map = px.choropleth_mapbox(
        real_map_data,
        geojson=taiwan_geojson,
        locations='district',
        featureidkey='properties.name',
        color='donation_total',
        color_continuous_scale='Blues',  # 可以改成 'Viridis' 或 'Plasma' 更科技感
        range_color=(real_map_data['donation_total'].min(), real_map_data['donation_total'].max()),
        hover_name='district',
        hover_data={'main_party': True, 'donation_total': ':,.0f 元'},
        zoom=7.8,
        center={"lat": 23.58, "lon": 120.98},
        opacity=0.75,
        mapbox_style="dark"  # 改成 dark 風格，更符合黑色主題
    )

    fig_map.update_traces(
        marker_line_width=1.2,
        marker_line_color='#00f0ff44',
    )

    fig_map.add_scattermapbox(
        lat=real_map_data['lat'],
        lon=real_map_data['lon'],
        mode='text',
        text=real_map_data['district'] + '<br>' + (real_map_data['donation_total'] / 1000000).round(0).astype(int).astype(str) + 'M',
        textfont=dict(size=10, color='#00f0ff'),
        hoverinfo='none'
    )

    fig_map.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        height=700,
        title="台灣選區捐款熱圖（真實資料版）",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e0e0ff'
    )

    st.plotly_chart(fig_map, use_container_width=True)

# ... (其他 tab 內容保持原樣或微調顏色)
