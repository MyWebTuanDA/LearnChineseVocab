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
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Hàm bổ trợ để đọc ngày tháng an toàn (Sửa lỗi bạn gặp phải)
def safe_parse_date(date_str):
    try:
        # Thử đọc định dạng có giờ phút
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        # Nếu không có giờ phút (dữ liệu cũ), tự thêm 00:00 vào
        return datetime.strptime(date_str, "%Y-%m-%d")

st.set_page_config(page_title="Học Tiếng Trung Pro", layout="wide")
st.title("🇨🇳 Hệ thống Ôn tập Level-Up")

data = load_data()

tab1, tab2, tab3 = st.tabs(["➕ Thêm từ", "🧠 Ôn tập theo Level", "📚 Thư viện"])

with tab1:
    st.header("Thêm từ vựng mới")
    c1, c2 = st.columns(2)
    with c1: vi = st.text_input("Nghĩa Tiếng Việt:")
    with c2: cn = st.text_input("Từ Tiếng Trung:")
    
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

with tab2:
    now = datetime.now()
    # SỬA LỖI TẠI ĐÂY: Dùng hàm safe_parse_date để lọc từ đến hạn
    due_list = [vi for vi, info in data.items() if safe_parse_date(info["next_review"]) <= now]

    if not due_list:
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
            st.subheader(f"Level {data[word]['level']} | Nghĩa: :red[{word}]")
            
            user_input = st.text_input("Nhập tiếng Trung:", key=f"re_{word}_{idx}")
            
            if st.button("Kiểm tra"):
                st.session_state.is_answered = True
            
            if st.session_state.is_answered:
                correct = data[word]["chinese"]
                if user_input.strip() == correct:
                    st.success("Chính xác!")
                    if word not in st.session_state.wrong_answers:
                        current_lvl = data[word]["level"]
                        new_lvl = min(current_lvl + 1, 6)
                        next_time = now + LEVEL_CONFIG[current_lvl]
                        data[word].update({
                            "level": new_lvl,
                            "next_review": next_time.strftime("%Y-%m-%d %H:%M")
                        })
                    else:
                        data[word].update({
                            "level": 1,
                            "next_review": (now + LEVEL_CONFIG[1]).strftime("%Y-%m-%d %H:%M")
                        })
                else:
                    st.error(f"Sai rồi! Đáp án là: {correct}")
                    data[word].update({
                        "level": 1,
                        "next_review": (now + LEVEL_CONFIG[1]).strftime("%Y-%m-%d %H:%M")
                    })
                    if word not in st.session_state.wrong_answers:
                        st.session_state.wrong_answers.append(word)
                
                if st.button("Tiếp theo"):
                    save_data(data)
                    st.session_state.current_idx += 1
                    st.session_state.is_answered = False
                    st.rerun()
        else:
            if st.session_state.wrong_answers:
                st.warning(f"Đã hết từ lượt 1. Bây giờ hãy làm lại {len(st.session_state.wrong_answers)} câu bạn đã sai nhé!")
                if st.button("Bắt đầu sửa lỗi"):
                    st.session_state.review_queue = st.session_state.wrong_answers.copy()
                    st.session_state.wrong_answers = [] # Reset để bắt đầu lượt kiểm tra lại mới
                    st.session_state.current_idx = 0
                    st.rerun()
            else:
                st.balloons()
                st.success("Tuyệt vời! Bạn đã hoàn thành sạch sẽ các từ lượt này.")
                if st.button("Kết thúc phiên học"):
                    # Dọn dẹp session để lần sau vào lại từ đầu
                    for key in ['review_queue', 'wrong_answers', 'current_idx', 'is_answered']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

with tab3:
    st.header("Quản lý kho từ")
    if data:
        df_list = [{"Từ": k, "Level": v["level"], "Hẹn ôn tập": v["next
