import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd # Dùng để hiện bảng từ vựng cho đẹp

FILE_NAME = "flashcards.json"

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

def sm2_update(is_correct, rep, interval, ease):
    if is_correct:
        if rep == 0: interval = 1
        elif rep == 1: interval = 6
        else: interval = int(interval * ease)
        rep += 1
        ease += 0.1
    else:
        rep = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
    return rep, interval, ease

st.set_page_config(page_title="Học Tiếng Trung SRS", page_icon="🇨🇳", layout="wide")
st.title("🇨🇳 Hệ thống Flashcard Tiếng Trung Thông Minh")

data = load_data()

# Tạo 3 Tab để quản lý
tab1, tab2, tab3 = st.tabs(["➕ Thêm từ", "🧠 Ôn tập (SRS)", "📚 Thư viện của tôi"])

# --- TAB 1: THÊM TỪ ---
with tab1:
    st.header("Thêm Flashcard mới")
    col_a, col_b = st.columns(2)
    with col_a:
        vi_word = st.text_input("Nghĩa Tiếng Việt (Ví dụ: Trái táo):")
    with col_b:
        cn_word = st.text_input("Từ Tiếng Trung (Ví dụ: 苹果):")
    
    if st.button("Lưu vào bộ nhớ"):
        if vi_word and cn_word:
            data[vi_word] = {
                "chinese": cn_word.strip(),
                "repetition": 0, "interval": 0, "ease": 2.5,
                "next_review": datetime.now().strftime("%Y-%m-%d")
            }
            save_data(data)
            st.success(f"Đã lưu thành công từ: {vi_word}")
        else:
            st.warning("Vui lòng không để trống ô nào.")

# --- TAB 2: ÔN TẬP ---
with tab2:
    st.header("Chế độ ôn tập")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Lựa chọn chế độ ôn tập
    mode = st.radio("Chọn chế độ:", ["Đúng lịch (SRS)", "Ôn tập tất cả (Cấp tốc)"], horizontal=True)
    
    if mode == "Đúng lịch (SRS)":
        due_words = [vi for vi, info in data.items() if info["next_review"] <= today]
        st.caption("Chế độ này giúp bạn ghi nhớ lâu dài theo khoa học.")
    else:
        due_words = list(data.keys())
        st.caption("Chế độ này giúp bạn xem lại tất cả các từ đang có.")

    if not due_words:
        st.info("Trống trải quá! Hãy thêm từ mới hoặc quay lại vào ngày mai.")
    else:
        if 'idx' not in st.session_state: st.session_state.idx = 0
        if 'is_checked' not in st.session_state: st.session_state.is_checked = False

        # Đảm bảo index không vượt quá số lượng từ
        if st.session_state.idx >= len(due_words):
            st.session_state.idx = 0

        word = due_words[st.session_state.idx]
        st.markdown(f"### Nghĩa tiếng Việt: <span style='color:red'>{word}</span>", unsafe_allow_html=True)
        
        user_ans = st.text_input("Nhập chữ Hán tương ứng:", key=f"input_{st.session_state.idx}")
        
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("Kiểm tra"):
                st.session_state.is_checked = True
        
        if st.session_state.is_checked:
            correct = data[word]["chinese"]
            if user_ans.strip() == correct:
                st.success("🎉 Chính xác!")
            else:
                st.error(f"❌ Sai rồi. Đáp án đúng là: {correct}")
            
            st.info(f"💡 Gợi ý: {word} -> {correct}")
            
            if st.button("Từ tiếp theo ➡️"):
                # Cập nhật thuật toán (chỉ cập nhật nếu ở chế độ SRS)
                if mode == "Đúng lịch (SRS)":
                    rep, inter, ease = sm2_update(user_ans.strip() == correct, data[word]["repetition"], data[word]["interval"], data[word]["ease"])
                    data[word].update({
                        "repetition": rep, "interval": inter, "ease": ease,
                        "next_review": (datetime.now() + timedelta(days=inter)).strftime("%Y-%m-%d")
                    })
                    save_data(data)
                
                st.session_state.idx += 1
                st.session_state.is_checked = False
                st.rerun()

# --- TAB 3: THƯ VIỆN ---
with tab3:
    st.header("Danh sách từ vựng của bạn")
    if not data:
        st.write("Bạn chưa có từ nào trong kho.")
    else:
        # Chuyển đổi dữ liệu sang bảng để xem cho dễ
        df_list = []
        for vi, info in data.items():
            df_list.append({
                "Tiếng Việt": vi,
                "Tiếng Trung": info["chinese"],
                "Lần ôn tiếp theo": info["next_review"],
                "Độ thuộc": f"{info['repetition']} lần đúng"
            })
        df = pd.DataFrame(df_list)
        st.table(df) # Hiện bảng danh sách từ
        
        # Thêm nút xóa dữ liệu nếu muốn làm lại từ đầu
        if st.button("Xóa toàn bộ từ vựng (Cẩn thận!)"):
            save_data({})
            st.rerun()
