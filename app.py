import streamlit as st
import pandas as pd

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="AI Exercise Advisor", page_icon="💪", layout="centered")

# --- 2. โหลดไฟล์ Excel ---
@st.cache_data
def load_data():
    try:
        # เปลี่ยนชื่อไฟล์ให้ตรงกับที่คุณอัปโหลด คือ "project.xlsx"
        df = pd.read_excel("project.xlsx") 
        
        # คลีนข้อมูล (ลบช่องว่างส่วนเกินเผื่อพิมพ์ผิดใน Excel)
        df.columns = df.columns.str.strip()
        for col in ['ความเหนื่อยล้า', 'การพักผ่อน', 'ค่า BMI']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                
        return df
    except FileNotFoundError:
        st.error("❌ ไม่พบไฟล์ Excel! กรุณาตรวจสอบว่าได้อัปโหลดไฟล์ 'project.xlsx' ขึ้น GitHub แล้ว")
        return pd.DataFrame() 

df_rules = load_data()

# --- 3. ฟังก์ชันประมวลผล AI ---
def get_ai_recommendation(bmi, sleep, fatigue):
    if df_rules.empty:
        return "⚠️ ระบบไม่พร้อมใช้งาน (ไม่พบฐานข้อมูล Excel)"

    # 3.1 แปลงค่าตัวเลขเป็นกลุ่ม (ต้องตรงกับคำใน Excel)
    if bmi < 18.5: 
        bmi_cat = "ผอม"
    elif 18.5 <= bmi <= 22.9: 
        bmi_cat = "ปกติ"
    elif 23.0 <= bmi <= 24.9: 
        bmi_cat = "ท้วม"
    elif 25.0 <= bmi <= 29.9: 
        bmi_cat = "อ้วน 1"
    else: 
        bmi_cat = "อ้วน 2"

    if sleep < 6: 
        sleep_cat = "น้อย"
    elif 6 <= sleep <= 7: 
        sleep_cat = "ปานกลาง"
    else: 
        sleep_cat = "มาก"

    if fatigue >= 7: 
        fatigue_cat = "มาก"
    elif 4 <= fatigue <= 6: 
        fatigue_cat = "ปานกลาง"
    else: 
        fatigue_cat = "น้อย"

    # 3.2 ค้นหาเงื่อนไขใน Excel ที่ตรงกับข้อมูล
    try:
        matched_rule = df_rules[
            (df_rules['ความเหนื่อยล้า'] == fatigue_cat) & 
            (df_rules['การพักผ่อน'] == sleep_cat) & 
            (df_rules['ค่า BMI'] == bmi_cat)
        ]
        
        # 3.3 ส่งผลลัพธ์กลับไป
        if not matched_rule.empty:
            return matched_rule['คำแนะนำ'].values[0]
        else:
            return f"⚠️ ไม่พบคำแนะนำที่ตรงกัน (ความเหนื่อยล้า={fatigue_cat}, การพักผ่อน={sleep_cat}, BMI={bmi_cat}) โปรดเช็คคำในไฟล์ Excel"
    except KeyError as e:
        return f"⚠️ ชื่อคอลัมน์ใน Excel ไม่ถูกต้อง: {e} (ต้องเป็น: ความเหนื่อยล้า, การพักผ่อน, ค่า BMI, คำแนะนำ)"

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
    st.write("กรุณากรอกข้อมูลเพื่อเริ่มต้นการวิเคราะห์")
    
    weight = st.number_input("น้ำหนัก (กก.)", min_value=30.0, max_value=200.0, value=65.0)
    height = st.number_input("ส่วนสูง (ซม.)", min_value=100.0, max_value=250.0, value=170.0)
    
    bmi = weight / ((height/100)**2)
    st.session_state.bmi = bmi
    
    st.subheader(f"ค่า BMI ของคุณคือ: {bmi:.2f}")
    
    if st.button("ไปต่อยังขั้นตอนถัดไป ➡️"):
        go_to_page2()

# หน้าที่ 2: การพักผ่อน และ ความเหนื่อยล้า
elif st.session_state.page == 2:
    st.title("Step 2: ประเมินสภาพร่างกายวันนี้ 🔋")
    st.write(f"ค่า BMI ปัจจุบัน: **{st.session_state.bmi:.2f}**")
    
    sleep_hours = st.slider("เมื่อคืนคุณนอนหลับกี่ชั่วโมง?", 0.0, 12.0, 7.0, step=0.5)
    fatigue_score = st.slider("ระดับความเหนื่อยล้าตอนนี้ (1-10)?", 1, 10, 3)
    
    st.info("คำอธิบาย: 1 = สดชื่นมาก, 10 = เพลียจนจะหลับ")

    if st.button("วิเคราะห์ผลลัพธ์จาก AI ✨"):
        st.divider()
        st.header("💡 คำแนะนำจาก AI")
        
        result = get_ai_recommendation(st.session_state.bmi, sleep_hours, fatigue_score)
        
        # ตกแต่งกล่องข้อความตามระดับความสำคัญ
        if "🛑" in str(result):
            st.error(result)
        elif "⚠️" in str(result):
            st.warning(result)
        else:
            st.success(result)
            st.balloons()

    st.write("") 
    if st.button("⬅️ ย้อนกลับไปหน้าแรก"):
        reset_app()
