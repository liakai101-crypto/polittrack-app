import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from io import BytesIO
import datetime
import base64
# 美化介面：藍綠色主題
st.markdown("""
<style>
    .stApp {
        background-color: #f0f8ff;  /* 淺藍背景，像天空透明 */
    }
    .css-1d391kg {  /* 側邊欄 */
        background-color: #e0f7fa;  /* 淺藍綠側邊欄 */
    }
    h1, h2, h3, h4 {
        color: #00695c;  /* 深綠標題 */
    }
    .stButton > button {
        background-color: #26a69a;  /* 按鈕藍綠色 */
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background-color: #00897b;  /* 滑鼠移上去更深 */
    }
    .stSidebar .sidebar-content {
        background-color: #e0f7fa;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 登入功能 ====================
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

# ==================== 讀取資料 ====================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("polittrack_data.csv", encoding='utf-8-sig')
        return df
    except FileNotFoundError:
        st.error("找不到 polittrack_data.csv")
        return pd.DataFrame()

df = load_data()

# 最後更新時間（模擬檔案修改時間）
last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# 選區地圖資料（模擬）
map_data = pd.DataFrame({
    'district': ['台北市', '新北市', '全國', '台中市', '高雄市'],
    'donation_total': [300000000, 250000000, 500000000, 150000000, 120000000],
    'lat': [25.0330, 25.0120, 23.6978, 24.1477, 22.6273],
    'lon': [121.5654, 121.4589, 120.9600, 120.6736, 120.3133]
})

st.title('Taiwan PoliTrack - 台灣政治透明平台')
# 加 logo（台灣國旗或資料圖示）
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Flag_of_the_Republic_of_China.svg/320px-Flag_of_the_Republic_of_China.svg.png", width=80)
st.markdown("### 台灣政治透明平台 PoliTrack")
st.markdown("""
**平台中立聲明**  
Taiwan PoliTrack 僅呈現政府公開資料（如監察院政治獻金、財產申報、立法院開放資料等），  
不添加任何主觀評論、不做立場傾向、不涉及政治宣傳。  
所有資料皆標註來源，使用者可自行驗證。  
若發現錯誤，請聯絡我們（未來加回報表單）。  
本平台目標：促進公民資訊透明與參與。
""")

# 登出按鈕
if st.sidebar.button("登出"):
    st.session_state.logged_in = False
    st.rerun()

# 顯示最後更新時間
st.sidebar.info(f"資料最後更新：{last_update}")

# ==================== 進階搜尋與篩選 ====================
st.sidebar.header("進階搜尋與篩選")

search_name = st.sidebar.text_input("姓名包含")
search_party = st.sidebar.selectbox("黨籍", ["全部"] + list(df['party'].unique()) if 'party' in df else ["全部"])
search_donor_type = st.sidebar.selectbox("捐款來源類型", ["全部", "企業", "個人", "團體"])
search_year = st.sidebar.slider("捐款年份範圍", int(df['donation_year'].min()) if 'donation_year' in df else 2020, 
                                int(df['donation_year'].max()) if 'donation_year' in df else 2025, (2020, 2025))
search_donation_min = st.sidebar.number_input("捐款總額最低", value=0)
search_donation_max = st.sidebar.number_input("捐款總額最高", value=1000000000)
search_area = st.sidebar.selectbox("選區", ["全部"] + list(df['district'].unique()) if 'district' in df else ["全部"])

sort_by = st.sidebar.selectbox("排序方式", ["無排序", "捐款金額降序", "財產增長率降序", "提案數降序"])

# 重置篩選按鈕
if st.sidebar.button("重置篩選"):
    st.rerun()

# 過濾資料
filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_name, na=False)]
if search_party != "全部":
    filtered_df = filtered_df[filtered_df['party'] == search_party]
if search_donor_type != "全部":
    filtered_df = filtered_df[filtered_df['donor_type'] == search_donor_type]
if 'donation_year' in filtered_df:
    filtered_df = filtered_df[(filtered_df['donation_year'] >= search_year[0]) & (filtered_df['donation_year'] <= search_year[1])]
filtered_df = filtered_df[(filtered_df['donation_total'] >= search_donation_min) & (filtered_df['donation_total'] <= search_donation_max)]
if search_area != "全部":
    filtered_df = filtered_df[filtered_df['district'] == search_area]

# 排序
if sort_by == "捐款金額降序":
    filtered_df = filtered_df.sort_values('donation_total', ascending=False)
elif sort_by == "財產增長率降序":
    filtered_df['growth_rate'] = (filtered_df['assets_2025'] - filtered_df['assets_2024']) / filtered_df['assets_2024'] * 100
    filtered_df = filtered_df.sort_values('growth_rate', ascending=False)
elif sort_by == "提案數降序":
    filtered_df['proposal_count'] = filtered_df['legislation_record'].str.extract('(\d+)').astype(float)
    filtered_df = filtered_df.sort_values('proposal_count', ascending=False)

# ==================== 主頁面內容 ====================
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

    st.subheader('捐款來源比例')
    donor_type_counts = filtered_df['donor_type'].value_counts()
    fig_pie = px.pie(donor_type_counts, values=donor_type_counts.values, names=donor_type_counts.index, title='捐款來源比例')
    st.plotly_chart(fig_pie)

    st.subheader('黨派捐款比較')
    party_sum = filtered_df.groupby('party')['donation_total'].sum().reset_index()
    fig_party = px.bar(party_sum, x='party', y='donation_total', title='各黨派總捐款金額')
    st.plotly_chart(fig_party)

    st.subheader('捐款年份變化')
    year_sum = filtered_df.groupby('donation_year')['donation_total'].sum().reset_index()
    fig_time = px.line(year_sum, x='donation_year', y='donation_total', title='年度捐款總額變化')
    st.plotly_chart(fig_time)

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

    col1, col2 = st.columns(2)
    with col1:
        if st.button('下載完整 CSV'):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("下載 CSV", csv, "polittrack_data.csv", "text/csv")

    with col2:
        selected_name = st.selectbox("選擇候選人匯出報告", df['name'].unique())
        if st.button('匯出 PDF 報告'):
            selected = df[df['name'] == selected_name].iloc[0]
            st.write("生成 PDF 中...")

            pdf_content = f"""
            Taiwan PoliTrack 報告
            姓名: {selected['name']}
            黨籍: {selected['party']}
            捐款總額: {selected['donation_total']}
            財產 (2025): {selected['assets_2025']}
            立法紀錄: {selected['legislation_record']}
            """
            b64 = base64.b64encode(pdf_content.encode()).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="report_{selected_name}.pdf">下載 PDF</a>', unsafe_allow_html=True)

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後重新執行程式即可生效。")
