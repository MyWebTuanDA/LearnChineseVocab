import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd

FILE_NAME = "flashcards.json"

# Cấu hình các mốc thời gian theo Level (Level: Khoảng thời gian chờ)
LEVEL_CONFIG = {
    1: timedelta(hours=2),
    2: timedelta(days=1),
    3: timedelta(days=2),
    4: timedelta(days=3),
    5: timedelta(days=5),
    6: timedelta(days=365) # Level 6 là mức cao nhất, xem lại sau 1 năm
}

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

st.set_page_config(page_title="Học Tiếng Trung Pro", layout="wide")
st.title("🇨🇳 Hệ thống Ôn tập Level-Up")

data = load_data()

tab1, tab2, tab3 = st.tabs(["➕ Thêm từ", "🧠 Ôn tập theo Level", "📚 Thư viện"])

# --- TAB 1: THÊM TỪ (Mặc định Level 1) ---
with tab1:
    st.header("Thêm từ vựng mới")
    c1, c2 = st.columns(2)
    with c1: vi = st.text_input("Nghĩa Tiếng Việt:")
    with c2: cn = st.text_input("Từ Tiếng Trung:")
    
    if st.button("Lưu từ vựng"):
        if vi and cn:
            # Từ mới luôn ở Level 1 và có thể học ngay lập tức
            data[vi] = {
                "chinese": cn.strip(),
                "level": 1,
                "next_review": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_data(data)
            st.success(f"Đã thêm '{vi}' vào Level 1")
        else:
            st.error("Vui lòng điền đủ thông tin.")

# --- TAB 2: ÔN TẬP (Logic Vòng lặp và Level) ---
with tab2:
    now = datetime.now()
    # Lọc từ đến hạn (next_review <= hiện tại)
    due_list = [vi for vi, info in data.items() if datetime.strptime(info["next_review"], "%Y-%m-%d %H:%M") <= now]

    if not due_list:
        st.info("Chưa có từ nào đến hạn ôn tập. Hãy nghỉ ngơi!")
    else:
        # Khởi tạo danh sách câu sai trong session_state nếu chưa có
        if 'review_queue' not in st.session_state:
            st.session_state.review_queue = due_list.copy() # Danh sách từ cần học trong lượt này
            st.session_state.wrong_answers = [] # Lưu những từ bị sai để làm lại cuối buổi
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
                    # Nếu từ này không nằm trong danh sách "đã từng sai" của lượt này thì mới lên cấp
                    if word not in st.session_state.wrong_answers:
                        current_lvl = data[word]["level"]
                        new_lvl = min(current_lvl + 1, 6)
                        next_time = now + LEVEL_CONFIG[current_lvl]
                        data[word].update({
                            "level": new_lvl,
                            "next_review": next_time.strftime("%Y-%m-%d %H:%M")
                        })
                    # Nếu là câu vừa sai nay làm lại cho đúng, nó vẫn ở Level 1 và hẹn 2 tiếng sau
                    else:
                        data[word].update({
                            "level": 1,
                            "next_review": (now + LEVEL_CONFIG[1]).strftime("%Y-%m-%d %H:%M")
                        })
                else:
                    st.error(f"Sai rồi! Đáp án là: {correct}")
                    # Đưa về level 1 và cho vào danh sách câu sai để làm lại cuối buổi
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
            # Khi đã đi hết danh sách ban đầu
            if st.session_state.wrong_answers:
                st.warning(f"Bạn đã hoàn thành lượt đầu, nhưng có {len(st.session_state.wrong_answers)} câu sai cần làm lại ngay!")
                if st.button("Làm lại các câu sai"):
                    st.session_state.review_queue = st.session_state.wrong_answers.copy()
                    # Giữ nguyên danh sách wrong_answers để không cho lên cấp trong lượt làm lại
                    st.session_state.current_idx = 0
                    st.rerun()
            else:
                st.balloons()
                st.success("Chúc mừng! Bạn đã thuộc hết từ vựng của lượt này.")
                if st.button("Kết thúc phiên ôn tập"):
                    del st.session_state.review_queue
                    del st.session_state.wrong_answers
                    st.rerun()

# --- TAB 3: THƯ VIỆN ---
with tab3:
    st.header("Quản lý kho từ")
    if data:
        df_list = [{"Từ": k, "Level": v["level"], "Hẹn ôn tập": v["next_review"]} for k, v in data.items()]
        st.table(pd.DataFrame(df_list))
    if st.button("Xóa sạch dữ liệu"):
        save_data({})
        st.rerun()
