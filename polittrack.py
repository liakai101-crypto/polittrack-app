import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from io import BytesIO

# ==================== 登入功能（簡單版） ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Taiwan PoliTrack 登入")
    username = st.text_input("使用者名稱")
    password = st.text_input("密碼", type="password")
    if st.button("登入"):
        if username == "admin" and password == "poli2026":  # 改成你想要的帳密
            st.session_state.logged_in = True
            st.success("登入成功！")
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")

if not st.session_state.logged_in:
    login()
    st.stop()

# ==================== 從 CSV 讀取資料 ====================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("polittrack_data.csv")
        return df
    except FileNotFoundError:
        st.error("找不到 polittrack_data.csv 檔案，請放在桌面並重新執行。")
        return pd.DataFrame()

df = load_data()

# 選區地圖資料（模擬）
map_data = pd.DataFrame({
    '選區': ['台北市', '新北市', '全國', '台中市', '高雄市'],
    '捐款總額': [300000000, 250000000, 500000000, 150000000, 120000000],
    'lat': [25.0330, 25.0120, 23.6978, 24.1477, 22.6273],
    'lon': [121.5654, 121.4589, 120.9600, 120.6736, 120.3133]
})

st.title('Taiwan PoliTrack - 台灣政治透明平台（完整版）')

# 登出按鈕
if st.sidebar.button("登出"):
    st.session_state.logged_in = False
    st.rerun()

# 進階搜尋條件
st.sidebar.header("進階搜尋")
search_name = st.sidebar.text_input("姓名包含")
search_party = st.sidebar.selectbox("黨籍", ["全部"] + list(df['黨籍'].unique()))
search_donation_min = st.sidebar.number_input("捐款總額最低", value=0)
search_donation_max = st.sidebar.number_input("捐款總額最高", value=1000000000)
search_area = st.sidebar.selectbox("選區", ["全部"] + list(df['選區'].unique()))

# 過濾資料
filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df['姓名'].str.contains(search_name)]
if search_party != "全部":
    filtered_df = filtered_df[filtered_df['黨籍'] == search_party]
filtered_df = filtered_df[(filtered_df['捐款總額'] >= search_donation_min) & (filtered_df['捐款總額'] <= search_donation_max)]
if search_area != "全部":
    filtered_df = filtered_df[filtered_df['選區'] == search_area]

# 主內容
tab1, tab2, tab3, tab4 = st.tabs(["主查詢與視覺化", "大額捐款排行", "關聯分析與地圖", "完整資料庫"])

with tab1:
    st.header('🔍 查詢結果')
    st.write(f"找到 {len(filtered_df)} 筆資料")
    st.dataframe(filtered_df)

    st.subheader('財產趨勢圖')
    fig_trend = px.line(filtered_df, x='姓名', y=['財產 (2024)', '財產 (2025)'], title='財產變化')
    st.plotly_chart(fig_trend)

    st.subheader('捐款總額排行')
    fig_bar = px.bar(filtered_df.sort_values('捐款總額', ascending=False), x='姓名', y='捐款總額')
    st.plotly_chart(fig_bar)

with tab2:
    st.header('💰 大額捐款者排行榜')
    top_donors = filtered_df.sort_values('捐款金額', ascending=False).head(15)
    st.dataframe(top_donors[['姓名', '大額捐款者', '捐款金額']])
    fig_rank = px.bar(top_donors, x='大額捐款者', y='捐款金額', color='姓名')
    st.plotly_chart(fig_rank)

with tab3:
    st.header('🧩 關聯分析')
    G = nx.Graph()
    for idx, row in filtered_df.iterrows():
        G.add_edge(row['姓名'], row['企業捐款議題關聯'], weight=row['捐款金額']/1000000)

    pos = nx.spring_layout(G, seed=42)
    fig_net = go.Figure()
    # ... (保持你之前的美化網絡圖代碼，這裡省略以節省空間，你可以保留原版或再貼)
    st.plotly_chart(fig_net)

    st.subheader('選區金流地圖')
    fig_map = px.scatter_geo(map_data, lat='lat', lon='lon', size='捐款總額',
                             hover_name='選區', color='捐款總額',
                             projection="natural earth")
    fig_map.update_geos(fitbounds="locations", center=dict(lat=23.6978, lon=120.9600), projection_scale=20)
    st.plotly_chart(fig_map)

with tab4:
    st.header('📂 完整資料庫')
    st.dataframe(df)

    if st.button('下載 CSV'):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("下載", csv, "polittrack_data.csv", "text/csv")

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後重新執行程式即可生效。")