import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import pandas as pd

# 1. KẾT NỐI SUPABASE
# Thay bằng thông tin bạn lấy ở bước 4
url: str = "URL_CUA_BAN"
key: str = "KEY_CUA_BAN"
supabase: Client = create_client(url, key)

# 2. CẤU HÌNH LEVEL
LEVEL_CONFIG = {
    1: timedelta(hours=2), 2: timedelta(days=1), 3: timedelta(days=2),
    4: timedelta(days=3), 5: timedelta(days=5), 6: timedelta(days=365)
}

st.set_page_config(page_title="Chinese Pro DB", layout="wide")

# 3. QUẢN LÝ NGƯỜI DÙNG (Để mỗi người dùng một kho riêng)
st.sidebar.title("👤 Đăng nhập")
user_id = st.sidebar.text_input("Nhập Tên/Email của bạn:", value="guest_user")

# --- HÀM TƯƠNG TÁC DATABASE ---
def get_all_cards(uid):
    # Lấy toàn bộ từ của người dùng hiện tại
    response = supabase.table("flashcards").select("*").eq("user_id", uid).execute()
    return response.data

def add_card(uid, vi, cn):
    # Thêm từ mới vào DB
    data = {
        "user_id": uid, "vietnamese": vi, "chinese": cn,
        "level": 1, "next_review": datetime.now().isoformat()
    }
    supabase.table("flashcards").insert(data).execute()

def update_card(card_id, new_lvl, next_time):
    # Cập nhật Level và ngày hẹn
    supabase.table("flashcards").update({
        "level": new_lvl, 
        "next_review": next_time.isoformat()
    }).eq("id", card_id).execute()

# --- GIAO DIỆN ---
tab1, tab2, tab3 = st.tabs(["➕ Thêm từ", "🧠 Ôn tập", "📚 Kho từ của tôi"])

with tab1:
    st.header(f"Thêm từ cho: {user_id}")
    c1, c2 = st.columns(2)
    with c1: vi = st.text_input("Tiếng Việt:")
    with c2: cn = st.text_input("Tiếng Trung:")
    if st.button("Lưu lên Database"):
        if vi and cn:
            add_card(user_id, vi, cn)
            st.success("Đã lưu vĩnh viễn!")

with tab2:
    all_cards = get_all_cards(user_id)
    now = datetime.now()
    # Lọc từ đến hạn từ dữ liệu DB
    due_list = [c for c in all_cards if datetime.fromisoformat(c['next_review'].replace('Z', '+00:00')).replace(tzinfo=None) <= now]

    if not due_list and 'queue' not in st.session_state:
        st.info("Hết bài rồi! Database đang đợi bạn thêm từ mới.")
    else:
        if 'queue' not in st.session_state:
            st.session_state.queue = due_list
            st.session_state.wrongs = []
            st.session_state.curr_idx = 0

        q = st.session_state.queue
        i = st.session_state.curr_idx

        if i < len(q):
            item = q[i]
            st.subheader(f"Level {item['level']} | Từ: {item['vietnamese']}")
            ans = st.text_input("Nhập chữ Hán:", key=f"ans_{item['id']}")
            
            if st.button("Kiểm tra"):
                correct = item['chinese']
                if ans.strip() == correct:
                    st.success("Đúng!")
                    if item['id'] not in [w['id'] for w in st.session_state.wrongs]:
                        # Lên cấp
                        new_lvl = min(item['level'] + 1, 6)
                        wait = LEVEL_CONFIG.get(item['level'], timedelta(hours=2))
                        update_card(item['id'], new_lvl, now + wait)
                    else:
                        # Vừa sai xong làm lại thì giữ level 1
                        update_card(item['id'], 1, now + LEVEL_CONFIG[1])
                else:
                    st.error(f"Sai! Đáp án: {correct}")
                    update_card(item['id'], 1, now + LEVEL_CONFIG[1])
                    if item['id'] not in [w['id'] for w in st.session_state.wrongs]:
                        st.session_state.wrongs.append(item)
                
                if st.button("Tiếp theo"):
                    st.session_state.curr_idx += 1
                    st.rerun()
        else:
            if st.session_state.wrongs:
                if st.button("Ôn lại câu sai"):
                    st.session_state.queue = st.session_state.wrongs.copy()
                    st.session_state.wrongs = []
                    st.session_state.curr_idx = 0
                    st.rerun()
            else:
                st.balloons()
                if st.button("Xong lượt"):
                    del st.session_state.queue
                    st.rerun()
# --- HÀM XÓA TỪ (Thêm vào phần các hàm tương tác DB) ---
def delete_card(card_id):
    supabase.table("flashcards").delete().eq("id", card_id).execute()

# ... (Các phần code cũ giữ nguyên) ...

# --- TAB 3: THƯ VIỆN & QUẢN LÝ ---
with tab3:
    st.header(f"📚 Kho từ của {user_id}")
    
    # Lấy dữ liệu mới nhất từ Database
    data_db = get_all_cards(user_id)
    
    if not data_db:
        st.info("Kho từ đang trống.")
    else:
        # Tạo bảng dữ liệu để hiển thị
        df = pd.DataFrame(data_db)
        
        # Hiển thị danh sách từ kèm nút xóa
        for index, row in df.iterrows():
            with st.container():
                # Chia cột để hàng ngang đẹp hơn
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 3, 1])
                
                with col1:
                    st.write(f"**{row['vietnamese']}**")
                with col2:
                    st.write(f"{row['chinese']}")
                with col3:
                    st.write(f"Lvl: {row['level']}")
                with col4:
                    # Định dạng lại thời gian hiển thị cho dễ nhìn
                    next_time = datetime.fromisoformat(row['next_review'].replace('Z', '+00:00')).strftime("%d/%m %H:%M")
                    st.write(f"📅: {next_time}")
                with col5:
                    # Nút xóa cho từng từ
                    if st.button("Xóa", key=f"del_{row['id']}"):
                        delete_card(row['id'])
                        st.success(f"Đã xóa '{row['vietnamese']}'")
                        st.rerun() # Load lại trang để cập nhật danh sách
                st.divider() # Đường kẻ ngang phân cách các từ

    # Nút xóa tất cả (giữ lại để reset nhanh nếu cần)
    if st.button("🚨 Xóa sạch kho từ"):
        if st.confirm("Bạn có chắc chắn muốn xóa toàn bộ từ vựng không?"):
            supabase.table("flashcards").delete().eq("id", user_id).execute()
            st.rerun()
with tab3:
    st.header(f"Dữ liệu của {user_id}")
    data_db = get_all_cards(user_id)
    if data_db:
        st.dataframe(pd.DataFrame(data_db)[['vietnamese', 'chinese', 'level', 'next_review']])
