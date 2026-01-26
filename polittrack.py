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
        if username == "admin" and password == "poli2026":
            st.session_state.logged_in = True
            st.success("登入成功！")
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")

if not st.session_state.logged_in:
    login()
    st.stop()

# ==================== 從 CSV 讀取資料（用英文欄位） ====================
@st.cache_data
def load_data():
    try:
        # 用 utf-8-sig 處理 Windows 常見的 BOM 編碼問題
        df = pd.read_csv("polittrack_data.csv", encoding='utf-8-sig')
        return df
    except FileNotFoundError:
        st.error("找不到 polittrack_data.csv 檔案，請放在桌面並重新執行。")
        return pd.DataFrame()

df = load_data()

# 選區地圖資料（模擬）
map_data = pd.DataFrame({
    'district': ['台北市', '新北市', '全國', '台中市', '高雄市'],
    'donation_total': [300000000, 250000000, 500000000, 150000000, 120000000],
    'lat': [25.0330, 25.0120, 23.6978, 24.1477, 22.6273],
    'lon': [121.5654, 121.4589, 120.9600, 120.6736, 120.3133]
})

st.title('Taiwan PoliTrack - 台灣政治透明平台（完整版）')

# 登出按鈕
if st.sidebar.button("登出"):
    st.session_state.logged_in = False
    st.rerun()

# 進階搜尋條件（用英文欄位）
st.sidebar.header("進階搜尋")
search_name = st.sidebar.text_input("姓名包含")
search_party = st.sidebar.selectbox("黨籍", ["全部"] + list(df['party'].unique()) if 'party' in df else ["全部"])
search_donation_min = st.sidebar.number_input("捐款總額最低", value=0)
search_donation_max = st.sidebar.number_input("捐款總額最高", value=1000000000)
search_area = st.sidebar.selectbox("選區", ["全部"] + list(df['district'].unique()) if 'district' in df else ["全部"])

# 過濾資料
filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_name)]
if search_party != "全部":
    filtered_df = filtered_df[filtered_df['party'] == search_party]
filtered_df = filtered_df[(filtered_df['donation_total'] >= search_donation_min) & (filtered_df['donation_total'] <= search_donation_max)]
if search_area != "全部":
    filtered_df = filtered_df[filtered_df['district'] == search_area]

# 主內容 - 用 tabs 分頁
tab1, tab2, tab3, tab4 = st.tabs(["主查詢與視覺化", "大額捐款排行", "關聯分析與地圖", "完整資料庫"])

with tab1:
    st.header('查詢結果')
    st.write(f"找到 {len(filtered_df)} 筆資料")
    st.dataframe(filtered_df)

    st.subheader('財產趨勢圖')
    fig_trend = px.line(filtered_df, x='name', y=['assets_2024', 'assets_2025'], title='財產變化')
    st.plotly_chart(fig_trend)

    st.subheader('捐款總額排行')
    fig_bar = px.bar(filtered_df.sort_values('donation_total', ascending=False), x='name', y='donation_total')
    st.plotly_chart(fig_bar)

with tab2:
    st.header('大額捐款者排行榜')
    top_donors = filtered_df.sort_values('donation_amount', ascending=False).head(15)
    st.dataframe(top_donors[['name', 'top_donor', 'donation_amount']])
    fig_rank = px.bar(top_donors, x='top_donor', y='donation_amount', color='name')
    st.plotly_chart(fig_rank)

with tab3:
    st.header('關聯分析')
    G = nx.Graph()
    for idx, row in filtered_df.iterrows():
        G.add_edge(row['name'], row['association'], weight=row['donation_amount']/1000000)

    pos = nx.spring_layout(G, seed=42)
    fig_net = go.Figure()
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=2, color='#888'), hoverinfo='none', mode='lines')

    node_x, node_y, node_text, node_size, node_color = [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        degree = G.degree(node)
        node_size.append(degree * 20 + 20)
        node_color.append('blue' if '企業' in node else 'green')

    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', hoverinfo='text', text=node_text,
                            marker=dict(showscale=False, color=node_color, size=node_size, line_width=2))

    fig_net = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(showlegend=False, hovermode='closest', margin=dict(b=20,l=5,r=5,t=40),
                                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    st.plotly_chart(fig_net)

    st.subheader('選區金流地圖')
    fig_map = px.scatter_geo(map_data, lat='lat', lon='lon', size='donation_total',
                             hover_name='district', color='donation_total',
                             projection="natural earth")
    fig_map.update_geos(fitbounds="locations", center=dict(lat=23.6978, lon=120.9600), projection_scale=20)
    st.plotly_chart(fig_map)

with tab4:
    st.header('完整資料庫')
    st.dataframe(df)

    if st.button('下載 CSV'):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("下載", csv, "polittrack_data.csv", "text/csv")

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後重新執行程式即可生效。")
