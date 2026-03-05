import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="AI Exercise Advisor", page_icon="💪", layout="centered")

# --- 2. โหลดไฟล์ Excel ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("project.xlsx") 
        df.columns = df.columns.str.strip()
        for col in ['ความเหนื่อยล้า', 'การพักผ่อน', 'ค่า BMI']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("❌ ไม่พบไฟล์ Excel! กรุณาตรวจสอบว่าได้อัปโหลดไฟล์ 'project.xlsx' ขึ้น GitHub แล้ว")
        return pd.DataFrame() 

df_rules = load_data()

# --- 3. ฟังก์ชันประมวลผล AI (Expert System Logic) ---
def get_ai_recommendation(bmi, sleep_hours, fatigue_score):
    if df_rules.empty:
        return "⚠️ ระบบไม่พร้อมใช้งาน (ไม่พบฐานข้อมูล Excel)"

    # --- 3.1 AI ทำการแปลงข้อมูลดิบ (Raw Data) ให้เป็นระดับสถานะ (Categorization) ---
    
    # ประเมินเกณฑ์ BMI
    if bmi < 18.5: bmi_cat = "ผอม"
    elif 18.5 <= bmi <= 22.9: bmi_cat = "ปกติ"
    elif 23.0 <= bmi <= 24.9: bmi_cat = "ท้วม"
    elif 25.0 <= bmi <= 29.9: bmi_cat = "อ้วน 1"
    else: bmi_cat = "อ้วน 2"

    # ประเมินเกณฑ์การพักผ่อน
    if sleep_hours < 6: sleep_cat = "น้อย"
    elif 6 <= sleep_hours <= 7: sleep_cat = "ปานกลาง"
    else: sleep_cat = "มาก"

    # ประเมินเกณฑ์ความเหนื่อยล้า
    if fatigue_score >= 7: fatigue_cat = "มาก"
    elif 4 <= fatigue_score <= 6: fatigue_cat = "ปานกลาง"
    else: fatigue_cat = "น้อย"

    # --- 3.2 นำสถานะที่วิเคราะห์ได้ ไปเทียบกับ Rule Base ในฐานข้อมูล Excel ---
    try:
        matched_rule = df_rules[
            (df_rules['ความเหนื่อยล้า'] == fatigue_cat) & 
            (df_rules['การพักผ่อน'] == sleep_cat) & 
            (df_rules['ค่า BMI'] == bmi_cat)
        ]
        
        if not matched_rule.empty:
            return matched_rule['คำแนะนำ'].values[0]
        else:
            return f"⚠️ ไม่พบเงื่อนไขที่ตรงกัน (วิเคราะห์ได้เป็น: เหนื่อย={fatigue_cat}, นอน={sleep_cat}, BMI={bmi_cat})"
    except KeyError as e:
        return f"⚠️ ชื่อคอลัมน์ใน Excel ไม่ถูกต้อง: {e}"

# --- 4. ระบบจัดการหน้าเว็บ (Session State) ---
if 'page' not in st.session_state:
    st.session_state.page = 1

def go_to_page2():
    st.session_state.page = 2

def reset_app():
    st.session_state.page = 1

# --- 5. ส่วนแสดงผลหน้าจอ UI ---

# หน้าที่ 1: คำนวณ BMI
if st.session_state.page == 1:
    st.title("Step 1: คำนวณค่า BMI ของคุณ ⚖️")
    st.write("ระบบจะใช้ค่า BMI เพื่อประเมินความพร้อมของข้อต่อและระบบเผาผลาญ")
    
    weight = st.number_input("น้ำหนัก (กก.)", min_value=30.0, max_value=200.0, value=65.0)
    height = st.number_input("ส่วนสูง (ซม.)", min_value=100.0, max_value=250.0, value=170.0)
    
    bmi = weight / ((height/100)**2)
    st.session_state.bmi = bmi
    
    st.subheader(f"ดัชนีมวลกาย (BMI) ของคุณคือ: {bmi:.2f}")
    
    if st.button("บันทึกข้อมูลและไปขั้นตอนถัดไป ➡️"):
        go_to_page2()

# หน้าที่ 2: ประเมินการพักผ่อนและความเหนื่อยล้า
elif st.session_state.page == 2:
    st.title("Step 2: วิเคราะห์สภาวะร่างกาย 🧠")
    st.write("ให้ AI ช่วยวิเคราะห์ระดับความพร้อมของร่างกายคุณในวันนี้")
    
    st.divider()
    
    # --- ส่วนที่ 1: คำนวณการพักผ่อน ---
    st.subheader("💤 ข้อมูลการพักผ่อน")
    col1, col2 = st.columns(2)
    with col1:
        bed_time = st.time_input("เวลาเข้านอน", value=datetime.strptime("23:00", "%H:%M").time())
    with col2:
        wake_time = st.time_input("เวลาตื่นนอน", value=datetime.strptime("06:30", "%H:%M").time())
    
    # ลอจิกคำนวณชั่วโมงการนอน (รองรับการนอนข้ามวัน)
    dt_bed = datetime.combine(date.today(), bed_time)
    dt_wake = datetime.combine(date.today(), wake_time)
    if dt_wake < dt_bed:
        dt_wake += timedelta(days=1) # ถ้าเวลาตื่นน้อยกว่าเวลานอน แปลว่าตื่นอีกวันนึง
        
    sleep_hours = (dt_wake - dt_bed).total_seconds() / 3600
    st.info(f"⏳ ระบบประมวลผล: คุณนอนหลับไปทั้งหมด **{sleep_hours:.1f} ชั่วโมง**")
    
    st.divider()
    
    # --- ส่วนที่ 2: ประเมินความเหนื่อยล้า ---
    st.subheader("🔋 ระดับความเหนื่อยล้า (Fatigue Level)")
    fatigue_score = st.slider("ประเมินความรู้สึกของคุณตอนนี้ (1 = สดชื่นมาก, 10 = ล้าจนอยากพัก)", 1, 10, 3)
    
    st.divider()

    # ปุ่มประมวลผล
    if st.button("🚀 ให้ AI แนะนำการออกกำลังกาย"):
        st.header("💡 ผลการวิเคราะห์และคำแนะนำ")
        
        # ส่งข้อมูลดิบทั้งหมดเข้าฟังก์ชันสมองกล
        result = get_ai_recommendation(st.session_state.bmi, sleep_hours, fatigue_score)
        
        # แสดงผลตามระดับความปลอดภัย
        if "🛑" in str(result):
            st.error(result)
        elif "⚠️" in str(result):
            st.warning(result)
        else:
            st.success(result)
            st.balloons()

    st.write("") 
    if st.button("⬅️ เริ่มต้นใหม่"):
        reset_app()
