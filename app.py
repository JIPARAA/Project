import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, time

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

    # นำสถานะที่วิเคราะห์ได้ ไปเทียบกับ Rule Base ในฐานข้อมูล Excel
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
    
    # --- ส่วนที่ 1: กรอกเวลาเป็นตัวเลขทศนิยม ---
    st.subheader("💤 ข้อมูลการพักผ่อน (กรอกเป็นตัวเลข)")
    col1, col2 = st.columns(2)
    with col1:
        # รับค่าเป็นทศนิยม เช่น 23.31
        bed_input = st.number_input("เวลาเข้านอน (เช่น 23.30)", min_value=0.00, max_value=23.59, value=23.00, step=0.01, format="%.2f")
    with col2:
        wake_input = st.number_input("เวลาตื่นนอน (เช่น 06.00)", min_value=0.00, max_value=23.59, value=6.00, step=0.01, format="%.2f")
    
    # --- ระบบแปลงทศนิยมเป็นเวลา (แยกชั่วโมงและนาที) ---
    bed_h = int(bed_input)
    bed_m = int(round((bed_input - bed_h) * 100))
    
    wake_h = int(wake_input)
    wake_m = int(round((wake_input - wake_h) * 100))
    
    # เช็คความถูกต้อง (เผื่อผู้ใช้เผลอกรอกนาทีเกิน 59 เช่น 23.80)
    if bed_m >= 60 or wake_m >= 60:
        st.error("⚠️ กรุณากรอก 'นาที' ไม่เกิน 59 (หลังจุดทศนิยมต้องไม่เกิน .59 ครับ)")
        sleep_hours = 0.0 # กันระบบพัง
    else:
        # คำนวณเวลา
        dt_bed = datetime.combine(date.today(), time(bed_h, bed_m))
        dt_wake = datetime.combine(date.today(), time(wake_h, wake_m))
        if dt_wake < dt_bed:
            dt_wake += timedelta(days=1) # กรณีตื่นอีกวัน
            
        sleep_hours = (dt_wake - dt_bed).total_seconds() / 3600
        st.info(f"⏳ ระบบประมวลผล: คุณนอนหลับไปทั้งหมด **{sleep_hours:.2f} ชั่วโมง**")
    
    st.divider()
    
    # --- ส่วนที่ 2: ประเมินความเหนื่อยล้า ---
    st.subheader("🔋 ระดับความเหนื่อยล้า (Fatigue Level)")
    fatigue_score = st.slider("ประเมินความรู้สึกของคุณตอนนี้ (1 = สดชื่นมาก, 10 = ล้าจนอยากพัก)", 1, 10, 3)
    
    st.divider()

    # ปุ่มประมวลผล
    if st.button("🚀 ให้ AI แนะนำการออกกำลังกาย"):
        if bed_m >= 60 or wake_m >= 60:
            st.warning("กรุณาแก้ไขเวลาการนอนให้ถูกต้องก่อนประมวลผลครับ")
        else:
            st.header("💡 ผลการวิเคราะห์และคำแนะนำ")
            
            result = get_ai_recommendation(st.session_state.bmi, sleep_hours, fatigue_score)
            
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
