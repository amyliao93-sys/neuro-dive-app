import streamlit as st
import time
import json
import random
import re

# 1. 最優先執行：設定頁面 (防止被其他邏輯卡住)
st.set_page_config(page_title="ND // REBOOT", layout="wide", page_icon="⚡")

# 2. 直接先印出標題，確保畫面有東西
st.title("⚡ SYSTEM REBOOT_SEQUENCE_INIT")
st.write("介面渲染層... [OK]")

# 3. 延遲匯入 (Lazy Import) - 防止 import 失敗導致白畫面
try:
    from google import genai
    from google.genai import types
    from PIL import Image, ImageDraw, ImageFilter
    st.write("核心模組載入... [OK]")
except ImportError as e:
    st.error(f"❌ 模組載入失敗: {e}")
    st.stop()

# ==========================================
# 4. 邏輯函式區 (全部封裝，不裸露執行)
# ==========================================

def get_client():
    """安全獲取 Client"""
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None, "API Key 未設定"
    try:
        # 使用 v1alpha 以支援更多模型
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        return client, None
    except Exception as e:
        return None, str(e)

def create_fallback_glitch(stress_score=50):
    """本地繪圖保底機制"""
    width, height = 800, 450
    img = Image.new('RGB', (width, height), color=(5, 5, 10))
    draw = ImageDraw.Draw(img)
    line_count = int(stress_score * 2.0) + 30
    colors = [(0, 255, 65), (255, 0, 85), (0, 255, 255), (50, 50, 50)]
    
    for _ in range(line_count):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = x1 + random.randint(-200, 200)
        y2 = y1 
        w_line = random.randint(1, 4)
        c = random.choice(colors)
        draw.line([(x1, y1), (x2, y2)], fill=c, width=w_line)

    for _ in range(15):
        x = random.randint(0, width)
        y = random.randint(0, height)
        w = random.randint(30, 150)
        h = random.randint(5, 50)
        draw.rectangle([x, y, x+w, y+h], outline=(0, 255, 65), width=1)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    return img

def analyze_dream(client, text):
    """分析夢境"""
    sys_instruct = """
    You are 'ND // NEURO-DIVE'. Analyze dream. Output valid JSON:
    {"stress_score": int, "analysis_log": string, "image_prompt": string}
    """
    model_candidates = ['gemini-2.0-flash-lite-preview-02-05', 'gemini-2.5-flash', 'gemini-2.0-flash']
    
    for model in model_candidates:
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"User Dream: {text}",
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    response_mime_type="application/json"
                )
            )
            # 清理 JSON
            clean_text = re.sub(r'```json\s*|```\s*', '', response.text).strip()
            return json.loads(clean_text)
        except Exception as e:
            if "429" in str(e): time.sleep(1)
            continue
    return None

def generate_image(client, prompt, stress):
    """繪圖 (混合模式)"""
    try:
        # 嘗試標準繪圖
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        return response.generated_images[0].image, "CLOUD"
    except:
        pass
    
    try:
        # 嘗試預覽版繪圖
        response = client.models.generate_images(
            model='gemini-2.0-flash-exp-image-generation',
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        return response.generated_images[0].image, "CLOUD_EXP"
    except:
        return create_fallback_glitch(stress), "LOCAL_FALLBACK"

# ==========================================
# 5. 主程式介面
# ==========================================

# CSS 開關 (預設關閉，防止看不見)
use_style = st.checkbox("啟動 Cyberpunk 視覺模組 (Enable CSS)", value=True)

if use_style:
    st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00FF41; font-family: monospace; }
    .stTextInput textarea { background-color: #111 !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; }
    .stButton button { background-color: #000; color: #00FF41; border: 1px solid #00FF41; width: 100%; }
    .stButton button:hover { background-color: #00FF41; color: #000; }
    h1, h2, h3 { color: #00FF41 !important; }
    </style>
    """, unsafe_allow_html=True)

st.divider()

# 初始化 Client (放在這裡才安全)
client, err = get_client()

if err:
    st.error(f"⚠️ 系統初始化失敗: {err}")
else:
    st.caption("🟢 NETWORK: ONLINE | CLIENT: AUTHENTICATED")

    user_input = st.text_area("INPUT DREAM...", height=150, placeholder="輸入夢境...")
    
    if st.button("INITIALIZE_NEURAL_LINK"):
        if not user_input:
            st.warning("請輸入內容")
        elif not client:
            st.error("Client 未連接")
        else:
            progress = st.empty()
            progress.info("🔄 DECODING SIGNALS...")
            
            # 1. 分析
            analysis = analyze_dream(client, user_input)
            
            if analysis:
                progress.info("🔄 GENERATING VISUALS...")
                stress = analysis.get('stress_score', 50)
                
                # 2. 繪圖
                img, source = generate_image(client, analysis.get('image_prompt', 'glitch'), stress)
                
                progress.empty() # 清除進度條
                st.success("✅ NEURAL LINK ESTABLISHED")
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.image(img, caption=f"SOURCE: {source}", use_column_width=True)
                with c2:
                    st.metric("STRESS", f"{stress}/100")
                    st.code(analysis.get('analysis_log', '...'))
            else:
                progress.error("❌ 連線失敗 (請檢查 429/404 錯誤)")