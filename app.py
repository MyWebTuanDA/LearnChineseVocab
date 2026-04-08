import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd

FILE_NAME = "flashcards.json"

# Cấu hình các mốc thời gian theo Level
LEVEL_CONFIG = {
    1: timedelta(hours=2),
    2: timedelta(days=1),
    3: timedelta(days=2),
    4: timedelta(days=3),
    5: timedelta(days=5),
    6: timedelta(days=365)
}

def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                
            # --- BỘ LỌC VÁ DỮ LIỆU CŨ (Sửa lỗi KeyError) ---
            updated = False
            for word, info in loaded_data.items():
                if "level" not in info:
                    info["level"] = 1
                    updated = True
                if "next_review" not in info:
                    info["next_review"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    updated = True
            
            if updated:
                save_data(loaded_data)
            return loaded_data
        except:
            return {}
    return {}

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def safe_parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        return datetime.now() # Nếu lỗi định dạng thì cho ôn tập ngay

st.set_page_config(page_title="Học Tiếng Trung Pro", layout="wide")
st.title("🇨🇳 Hệ thống Ôn tập Level-Up")

data = load_data()

tab1, tab2, tab3 = st.tabs(["➕ Thêm từ", "🧠 Ôn tập theo Level", "📚 Thư viện"])

# --- TAB 1: THÊM TỪ ---
with tab1:
    st.header("Thêm từ vựng mới")
    c1, c2 = st.columns(2)
    with c1: vi = st.text_input("Nghĩa Tiếng Việt:", key="add_vi")
    with c2: cn = st.text_input("Từ Tiếng Trung:", key="add_cn")
    
    if st.button("Lưu từ vựng"):
        if vi and cn:
            data[vi] = {
                "chinese": cn.strip(),
                "level": 1,
                "next_review": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_data(data)
            st.success(f"Đã thêm '{vi}' vào Level 1")
        else:
            st.error("Vui lòng điền đủ thông tin.")

# --- TAB 2: ÔN TẬP ---
with tab2:
    now = datetime.now()
    due_list = [vi for vi, info in data.items() if safe_parse_date(info["next_review"]) <= now]

    if not due_list and 'review_queue' not in st.session_state:
        st.info("Chưa có từ nào đến hạn ôn tập. Hãy nghỉ ngơi!")
    else:
        if 'review_queue' not in st.session_state:
            st.session_state.review_queue = due_list.copy()
            st.session_state.wrong_answers = [] 
            st.session_state.current_idx = 0
            st.session_state.is_answered = False

        queue = st.session_state.review_queue
        idx = st.session_state.current_idx

        if idx < len(queue):
            word = queue[idx]
            st.subheader(f"Level {data[word].get('level', 1)} | Nghĩa: :red[{word}]")
            
            user_input = st.text_input("Nhập tiếng Trung:", key=f"input_{word}_{idx}")
            
            col_check, col_next = st.columns([1, 5])
            with col_check:
                if st.button("Kiểm tra"):
                    st.session_state.is_answered = True
            
            if st.session_state.is_answered:
                correct = data[word]["chinese"]
                is_correct = (user_input.strip() == correct)
                
                if is_correct:
                    st.success("Chính xác!")
                else:
                    st.error(f"Sai rồi! Đáp án là: {correct}")
                st.info(f"💡 Đáp án: {word} -> {correct}")

                if st.button("Tiếp theo ➡️"):
                    if is_correct:
                        if word not in st.session_state.wrong_answers:
                            curr_lvl = data[word].get('level', 1)
                            new_lvl = min(curr_lvl + 1, 6)
                            wait_time = LEVEL_CONFIG.get(curr_lvl, timedelta(hours=2))
                            data[word].update({
                                "level": new_lvl,
                                "next_review": (now + wait_time).strftime("%Y-%m-%d %H:%M")
                            })
                        else:
                            data[word].update({
                                "level": 1,
                                "next_review": (now + LEVEL_CONFIG[1]).strftime("%Y-%m-%d %H:%M")
                            })
                    else:
                        data[word].update({
                            "level": 1,
                            "next_review": (now + LEVEL_CONFIG[1]).strftime("%Y-%m-%d %H:%M")
                        })
                        if word not in st.session_state.wrong_answers:
                            st.session_state.wrong_answers.append(word)
                    
                    save_data(data)
                    st.session_state.current_idx += 1
                    st.session_state.is_answered = False
                    st.rerun()
        else:
            if st.session_state.wrong_answers:
                st.warning(f"Làm lại {len(st.session_state.wrong_answers)} câu sai!")
                if st.button("Bắt đầu sửa lỗi"):
                    st.session_state.review_queue = st.session_state.wrong_answers.copy()
                    st.session_state.wrong_answers = [] 
                    st.session_state.current_idx = 0
                    st.session_state.is_answered = False
                    st.rerun()
            else:
                st.balloons()
                st.success("Hoàn thành!")
                if st.button("Kết thúc"):
                    for key in ['review_queue', 'wrong_answers', 'current_idx', 'is_answered']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

# --- TAB 3: THƯ VIỆN ---
with tab3:
    st.header("Quản lý kho từ")
    if data:
        # Sử dụng .get() để lấy dữ liệu an toàn, tránh KeyError lần nữa
        df_list = []
        for k, v in data.items():
            df_list.append({
                "Từ": k, 
                "Level": v.get("level", 1), 
                "Hẹn ôn tập": v.get("next_review", "N/A")
            })
        st.table(pd.DataFrame(df_list))
    
    if st.button("Xóa sạch toàn bộ dữ liệu (Reset app)"):
        save_data({})
        st.rerun()
