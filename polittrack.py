import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
import datetime
from fpdf import FPDF

# ==================== 頁面設定與美化 ====================
st.set_page_config(
    page_title="Taiwan PoliTrack - 政治透明平台",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Flag_of_the_Republic_of_China.svg/32px-Flag_of_the_Republic_of_China.svg.png",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f0f8ff; }
    .css-1d391kg { background-color: #e0f7fa; }
    h1, h2, h3 { color: #00695c; }
    .stButton > button { background-color: #26a69a; color: white; border: none; }
    .stButton > button:hover { background-color: #00897b; }
    .stSidebar .sidebar-content { background-color: #e0f7fa; }
</style>
""", unsafe_allow_html=True)

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
st.sidebar.info(f"資料最後更新：{last_update}")

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

if st.sidebar.button("重置篩選"):
    st.rerun()

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

if sort_by == "捐款金額降序":
    filtered_df = filtered_df.sort_values('donation_total', ascending=False)
elif sort_by == "財產增長率降序":
    filtered_df['growth_rate'] = (filtered_df['assets_2025'] - filtered_df['assets_2024']) / filtered_df['assets_2024'] * 100
    filtered_df = filtered_df.sort_values('growth_rate', ascending=False)
elif sort_by == "提案數降序":
    filtered_df['proposal_count'] = filtered_df['legislation_record'].str.extract('(\d+)').astype(float)
    filtered_df = filtered_df.sort_values('proposal_count', ascending=False)

def add_warning(row):
    if row.get('donation_amount', 0) > 10000000 and '企業' in str(row.get('top_donor', '')) and '法案' in str(row.get('association', '')):
        return "⚠️ 異常捐款警示：金額高且議題高度相關"
    return ""

filtered_df['warning'] = filtered_df.apply(add_warning, axis=1)

map_data = pd.DataFrame({
    'district': ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '新竹市', '嘉義市', '宜蘭縣', '新竹縣', '苗栗縣', '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '臺東縣', '花蓮縣', '澎湖縣', '金門縣', '連江縣'],
    'donation_total': [850000000, 650000000, 450000000, 550000000, 380000000, 480000000, 120000000, 180000000, 150000000, 200000000, 220000000, 190000000, 280000000, 160000000, 140000000, 130000000, 170000000, 110000000, 130000000, 80000000, 90000000, 50000000],
    'lat': [25.0330, 25.0120, 24.9934, 24.1477, 22.9999, 22.6273, 25.1337, 24.8138, 23.4807, 24.7503, 24.8270, 24.5643, 24.0510, 23.9601, 23.7089, 23.4811, 22.5519, 22.7554, 23.9743, 23.5655, 24.4360, 26.1500],
    'lon': [121.5654, 121.4589, 121.2999, 120.6736, 120.2270, 120.3133, 121.7425, 120.9686, 120.4491, 121.7470, 121.0129, 120.8269, 120.4818, 120.9716, 120.4313, 120.4491, 120.4918, 121.1500, 121.6167, 119.5655, 118.3200, 119.9500],
    'main_party': ['國民黨', '國民黨', '民進黨', '民進黨', '民進黨', '民進黨', '國民黨', '民眾黨', '民進黨', '民進黨', '國民黨', '國民黨', '民進黨', '民進黨', '民進黨', '民進黨', '民進黨', '民進黨', '國民黨', '無黨籍', '國民黨', '國民黨']
})

tab1, tab2, tab3, tab4 = st.tabs(["主查詢與視覺化", "大額捐款排行", "選區金流地圖", "完整資料庫"])

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
    fig_pie = px.pie(donor_type_counts, values=donor_type_counts.values, names=donor_type_counts.index)
    st.plotly_chart(fig_pie)

    st.subheader('黨派捐款比較')
    party_sum = filtered_df.groupby('party')['donation_total'].sum().reset_index()
    fig_party = px.bar(party_sum, x='party', y='donation_total')
    st.plotly_chart(fig_party)

    st.subheader('捐款年份變化')
    year_sum = filtered_df.groupby('donation_year')['donation_total'].sum().reset_index()
    fig_time = px.line(year_sum, x='donation_year', y='donation_total')
    st.plotly_chart(fig_time)

with tab2:
    st.header('大額捐款者排行榜')
    top_donors = filtered_df.sort_values('donation_amount', ascending=False).head(15)
    st.dataframe(top_donors[['name', 'top_donor', 'donation_amount']])
    fig_rank = px.bar(top_donors, x='top_donor', y='donation_amount', color='name')
    st.plotly_chart(fig_rank)

with tab3:
    st.header('選區金流地圖（僅台灣領土）')
    
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
        range_color=(map_data['donation_total'].min(), map_data['donation_total'].max()),
        hover_name='district',
        hover_data=['main_party', 'donation_total'],
        zoom=7.8,
        center={"lat": 23.58, "lon": 120.98},
        opacity=0.85,
        mapbox_style="carto-positron"  # 簡單底圖，讓地圖更立體
    )

    # 加粗黑邊界，讓邊界超級清晰
    fig_map.update_traces(
        marker_line_width=2.5,         # 邊界粗細（可調到 3 或 4 更粗）
        marker_line_color='black',     # 邊界線改黑色
        selector=dict(type='choroplethmapbox')
    )

    # 加縣市名稱標籤，讓每個區域清楚可辨
    fig_map.add_scattermapbox(
        lat=map_data['lat'],
        lon=map_data['lon'],
        mode='text',
        text=map_data['district'],
        textfont=dict(size=11, color='black', family="Arial Black"),
        hoverinfo='none'
    )

    fig_map.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        height=700,
        title="台灣選區捐款熱圖（邊界強化版）"
    )

    st.plotly_chart(fig_map, use_container_width=True)

with tab4:
    st.header('完整資料庫')
    st.dataframe(df)

    col1, col2 = st.columns(2)
    with col1:
        if st.button('下載完整 CSV'):
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8')
            st.download_button("下載 CSV", csv, "polittrack_data.csv", "text/csv")

    with col2:
        selected_name = st.selectbox("選擇候選人匯出報告", df['name'].unique())
        if st.button('匯出 PDF 報告'):
            selected = df[df['name'] == selected_name].iloc[0]

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Taiwan PoliTrack 個人報告", ln=1, align='C')
            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"姓名: {selected['name']}", ln=1)
            pdf.cell(0, 10, f"黨籍: {selected['party']}", ln=1)
            pdf.cell(0, 10, f"捐款總額: {selected['donation_total']:,} 元", ln=1)
            pdf.cell(0, 10, f"財產 (2025): {selected['assets_2025']:,} 元", ln=1)
            pdf.cell(0, 10, f"立法紀錄: {selected['legislation_record']}", ln=1)
            pdf.cell(0, 10, f"警示: {selected.get('warning', '無異常')}", ln=1)

            pdf_output = BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)

            st.download_button(
                label="下載標準 PDF 報告",
                data=pdf_output,
                file_name=f"report_{selected_name}.pdf",
                mime="application/pdf"
            )

st.sidebar.info("資料從 polittrack_data.csv 讀取，用 Excel 更新後重新執行程式即可生效。")
