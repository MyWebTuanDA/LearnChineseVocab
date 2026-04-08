import streamlit as st
import json
from datetime import datetime, timedelta
import os

# Tên file lưu trữ từ vựng
FILE_NAME = "flashcards.json"

# Hàm đọc dữ liệu
def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Hàm lưu dữ liệu
def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Thuật toán Spaced Repetition (SuperMemo-2 đơn giản hóa)
def sm2_update(is_correct, rep, interval, ease):
    if is_correct:
        if rep == 0:
            interval = 1
        elif rep == 1:
            interval = 6
        else:
            interval = int(interval * ease)
        rep += 1
        ease += 0.1
    else:
        rep = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
    return rep, interval, ease

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="App Học Tiếng Trung", page_icon="🇨🇳")
st.title("📚 App Học Tiếng Trung (SRS)")

# Tải dữ liệu từ vựng hiện có
data = load_data()

# Chia làm 2 tab: Thêm từ và Ôn tập
tab1, tab2 = st.tabs(["➕ Thêm từ mới", "🧠 Ôn tập hôm nay"])

# TAB 1: THÊM TỪ
with tab1:
    st.header("Tạo Flashcard mới")
    vi_word = st.text_input("Nghĩa Tiếng Việt (Ví dụ: Xin chào):")
    cn_word = st.text_input("Từ Tiếng Trung (Ví dụ: 你好):")
    
    if st.button("Thêm vào kho từ"):
        if vi_word and cn_word:
            if vi_word in data:
                st.warning("Từ này đã có trong kho!")
            else:
                data[vi_word] = {
                    "chinese": cn_word.strip(),
                    "repetition": 0,
                    "interval": 0,
                    "ease": 2.5,
                    "next_review": datetime.now().strftime("%Y-%m-%d") # Cần ôn tập ngay hôm nay
                }
                save_data(data)
                st.success(f"Đã thêm: {vi_word} - {cn_word}")
        else:
            st.error("Vui lòng điền đầy đủ cả 2 ô.")

# TAB 2: ÔN TẬP
with tab2:
    st.header("Kiểm tra trí nhớ")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Lọc ra các từ cần ôn tập hôm nay (hoặc đã quá hạn)
    due_words = [vi for vi, info in data.items() if info["next_review"] <= today]
    
    if not due_words:
        st.info("🎉 Tuyệt vời! Bạn đã ôn tập xong tất cả các từ cho hôm nay. Hãy quay lại vào ngày mai nhé!")
    else:
        st.write(f"Bạn còn **{len(due_words)}** từ cần ôn tập.")
        st.divider()
        
        # Lấy từ đầu tiên trong danh sách cần ôn để hiển thị
        current_word = due_words[0]
        st.subheader(f"Nghĩa Tiếng Việt: **{current_word}**")
        
        # Tạo form nhập liệu
with st.form("review_form", clear_on_submit=True):
            answer = st.text_input("Nhập Tiếng Trung ứng với nghĩa trên:")
            submitted = st.form_submit_button("Kiểm tra")
            
            if submitted:
                # Xử lý logic đúng/sai
                is_correct = (answer.strip() == data[current_word]["chinese"])
                
                if is_correct:
                    st.success("✅ Chính xác!")
                else:
                    st.error(f"❌ Sai rồi! Đáp án đúng là: **{data[current_word]['chinese']}**")
                
                # Cập nhật thông số Spaced Repetition
                rep, inter, ease = sm2_update(
                    is_correct, 
                    data[current_word]["repetition"], 
                    data[current_word]["interval"], 
                    data[current_word]["ease"]
                )
                
                # Lưu thông số mới
                data[current_word]["repetition"] = rep
                data[current_word]["interval"] = inter
                data[current_word]["ease"] = ease
                
                # Tính ngày ôn tập tiếp theo
                next_date = datetime.now() + timedelta(days=inter)
                data[current_word]["next_review"] = next_date.strftime("%Y-%m-%d")
                
                save_data(data)
                
                # Tải lại trang để hiện từ tiếp theo
                st.rerun()
