import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from io import BytesIO
import datetime
import base64
from fpdf import FPDF  # 新增：用來生成真 PDF

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

# ==================== 美化介面：藍綠色主題 + 說明文字 ====================
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

# 加 logo（台灣國旗示意，可換成你喜歡的）
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Flag_of_the_Republic_of_China.svg/320px-Flag_of_the_Republic_of_China.svg.png", width=80)

st.title('Taiwan PoliTrack - 台灣政治透明平台')

# 加中立說明文字 + 資料來源連結按鈕
st.markdown("""
**平台中立聲明**  
本平台僅呈現政府公開資料，不添加任何主觀評論、不做立場傾向、不涉及政治宣傳。  
所有資料來源自監察院、立法院等官方公開平台，使用者可自行驗證。  
如有錯誤，請聯絡我們（未來加回報表單）。  
本平台目標：促進公民資訊透明與參與。
""")

# 加資料來源連結按鈕
col_link1, col_link2 = st.columns(2)
with col_link1:
    st.markdown("[監察院政治獻金公開平台](https://ardata.cy.gov.tw)")
with col_link2:
    st.markdown("[立法院開放資料平台](https://data.ly.gov.tw)")

# ==================== 讀取資料 + 最後更新時間 ====================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("polittrack_data.csv", encoding='utf-8-sig')
        return df
    except FileNotFoundError:
        st.error("找不到 polittrack_data.csv")
        return pd.DataFrame()

df = load_data()

# 最後更新時間（用現在時間模擬，未來可改讀檔案修改時間）
last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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

if st.sidebar.button("重置篩選"):
    st.rerun()

# 過濾資料（略，同前）

# ==================== 捐款異常警示（新功能） ====================
def add_warning(row):
    if row['donation_amount'] > 10000000 and '企業' in row['top_donor'] and '法案' in row['association']:
        return "⚠️ 異常捐款警示：金額高且議題高度相關"
    return ""

filtered_df['warning'] = filtered_df.apply(add_warning, axis=1)

# ==================== 主頁面內容（略，同前，但表格顯示 warning 欄） ====================
# ...（保持原來的 tab1~tab4 內容，但 tab1 的 st.dataframe 加 column_config 顯示 warning 紅色）
with tab1:
    st.dataframe(
        filtered_df,
        column_config={
            "warning": st.column_config.TextColumn("警示", width="medium")
        }
    )

# ==================== 真 PDF 匯出（使用 fpdf2） ====================
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
        pdf.cell(0, 10, f"警示: {selected['warning'] or '無異常'}", ln=1)

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        st.download_button(
            label="下載標準 PDF 報告",
            data=pdf_output,
            file_name=f"report_{selected_name}.pdf",
            mime="application/pdf"
        )
