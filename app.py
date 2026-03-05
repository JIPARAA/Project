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

    if bmi < 18.5: bmi_cat = "ผอม"
    elif 18.5 <= bmi <= 22.9: bmi_cat = "ปกติ"
    elif 23.0 <= bmi <= 24.9: bmi_cat = "ท้วม"
    elif 25.0 <= bmi <= 29.9: bmi_cat = "อ้วน 1"
    else: bmi_cat = "อ้วน 2"

    if sleep_hours < 6: sleep_cat = "น้อย"
    elif 6 <= sleep_hours <= 7: sleep_cat = "ปานกลาง"
    else: sleep_cat = "มาก"

    if fatigue_score >= 7: fatigue_cat = "มาก"
    elif 4 <= fatigue_score <= 6: fatigue_cat = "ปานกลาง"
    else: fatigue_cat = "น้อย"

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
    
    # --- ส่วนที่ 1: กรอกเวลาเป็นข้อความ ---
    st.subheader("💤 ข้อมูลการพักผ่อน")
    col1, col2 = st.columns(2)
    with col1:
        bed_input = st.text_input("เวลาเข้านอน (เช่น 23.30)", value="23.30")
    with col2:
        wake_input = st.text_input("เวลาตื่นนอน (เช่น 08.01)", value="08.01")
    
    # --- ระบบแปลงเวลาและตรวจสอบความถูกต้อง ---
    error_time = False
    sleep_hours = 0.0
    
    try:
        b_parts = bed_input.replace(':', '.').split('.')
        w_parts = wake_input.replace(':', '.').split('.')
        
        bed_h = int(b_parts[0])
        bed_m = int(b_parts[1]) if len(b_parts) > 1 else 0
        
        wake_h = int(w_parts[0])
        wake_m = int(w_parts[1]) if len(w_parts) > 1 else 0

        if bed_h >= 24 or wake_h >= 24 or bed_m >= 60 or wake_m >= 60:
            st.error("⚠️ กรุณากรอกเวลาให้ถูกต้อง (ชั่วโมง 0-23, นาที 0-59)")
            error_time = True
        else:
            dt_bed = datetime.combine(date.today(), time(bed_h, bed_m))
            dt_wake = datetime.combine(date.today(), time(wake_h, wake_m))
            if dt_wake < dt_bed:
                dt_wake += timedelta(days=1)
                
            # คำนวณเป็นวินาทีทั้งหมดก่อน
            total_seconds = (dt_wake - dt_bed).total_seconds()
            
            # เก็บค่าทศนิยมไว้ให้ AI ประมวลผลเหมือนเดิม
            sleep_hours = total_seconds / 3600
            
            # แปลงเป็น ชั่วโมง และ นาที สำหรับแสดงผลให้คนดู
            display_h = int(total_seconds // 3600)
            display_m = int((total_seconds % 3600) // 60)
            
            # แสดงผลแบบใหม่ อ่านง่าย ไม่งง
            st.info(f"⏳ ระบบประมวลผล: คุณนอนหลับไปทั้งหมด **{display_h} ชั่วโมง {display_m} นาที**")
            
    except Exception:
        st.error("⚠️ กรุณากรอกรูปแบบเวลาให้ถูกต้อง เช่น 23.30 หรือ 08.01")
        error_time = True
    
    st.divider()
    
    # --- ส่วนที่ 2: ประเมินความเหนื่อยล้า ---
    st.subheader("🔋 ระดับความเหนื่อยล้า (Fatigue Level)")
    fatigue_score = st.slider("ประเมินความรู้สึกของคุณตอนนี้ (1 = สดชื่นมาก, 10 = ล้าจนอยากพัก)", 1, 10, 3)
    
    st.divider()

    # ปุ่มประมวลผล
    if st.button("🚀 ให้ AI แนะนำการออกกำลังกาย"):
        if error_time:
            st.warning("กรุณาแก้ไขเวลาการนอนให้ถูกต้องก่อนให้ AI ประมวลผลครับ")
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
