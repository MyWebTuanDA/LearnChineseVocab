import streamlit as st
import json
from datetime import datetime, timedelta
import os

# Tên file lưu trữ từ vựng
FILE_NAME = "flashcards.json"

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
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

st.set_page_config(page_title="App Học Tiếng Trung", page_icon="🇨🇳")
st.title("📚 App Học Tiếng Trung (SRS)")

data = load_data()
tab1, tab2 = st.tabs(["➕ Thêm từ mới", "🧠 Ôn tập hôm nay"])

# TAB 1: THÊM TỪ (Giữ nguyên)
with tab1:
    st.header("Tạo Flashcard mới")
    vi_word = st.text_input("Nghĩa Tiếng Việt:")
    cn_word = st.text_input("Từ Tiếng Trung:")
    if st.button("Thêm vào kho từ"):
        if vi_word and cn_word:
            data[vi_word] = {
                "chinese": cn_word.strip(),
                "repetition": 0, "interval": 0, "ease": 2.5,
                "next_review": datetime.now().strftime("%Y-%m-%d")
            }
            save_data(data)
            st.success(f"Đã thêm: {vi_word}")
        else:
            st.error("Vui lòng điền đủ thông tin.")

# TAB 2: ÔN TẬP (Cập nhật logic Dừng để xem đáp án)
with tab2:
    st.header("Kiểm tra trí nhớ")
    today = datetime.now().strftime("%Y-%m-%d")
    due_words = [vi for vi, info in data.items() if info["next_review"] <= today]
    
    if not due_words:
        st.info("🎉 Bạn đã hoàn thành hết từ vựng hôm nay!")
    else:
        # Sử dụng session_state để lưu trạng thái đang kiểm tra hay chưa
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0
            st.session_state.checked = False

        word_to_review = due_words[st.session_state.current_index]
        st.subheader(f"Nghĩa Tiếng Việt: **{word_to_review}**")

        # Ô nhập liệu
        user_input = st.text_input("Nhập Tiếng Trung ứng với nghĩa trên:", key="input_box")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Kiểm tra"):
                st.session_state.checked = True
        
        if st.session_state.checked:
            correct_answer = data[word_to_review]["chinese"]
            is_correct = (user_input.strip() == correct_answer)

            if is_correct:
                st.success("✅ CHÍNH XÁC!")
            else:
                st.error("❌ CHƯA ĐÚNG!")
                # LUÔN HIỆN ĐÁP ÁN ĐÚNG Ở DƯỚI
            st.info(f"Đáp án đúng là: **{correct_answer}**")

            with col2:
                if st.button("Tiếp theo ➡️"):
                    # Cập nhật thuật toán SRS trước khi chuyển từ
                    rep, inter, ease = sm2_update(
                        is_correct, 
                        data[word_to_review]["repetition"], 
                        data[word_to_review]["interval"], 
                        data[word_to_review]["ease"]
                    )
                    data[word_to_review].update({
                        "repetition": rep, "interval": inter, "ease": ease,
                        "next_review": (datetime.now() + timedelta(days=inter)).strftime("%Y-%m-%d")
                    })
                    save_data(data)
                    
                    # Reset trạng thái để sang từ tiếp theo
                    st.session_state.checked = False
                    st.rerun()
