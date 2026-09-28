import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime, date

# =========================================================
# CẤU HÌNH STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Hotel Room Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# THÔNG TIN MYSQL AIVEN
# =========================================================

MYSQL_HOST = "mysql-1cc70107-anhthutran21092005-5a1e.h.aivencloud.com "
MYSQL_PORT = 12023
MYSQL_USER = "avnadmin"
MYSQL_PASSWORD = "AVNS_KO5XwLUd22vzEvBne42"

# Database mặc định của Aiven MySQL
MYSQL_DATABASE = "defaultdb"


# =========================================================
# KẾT NỐI MYSQL
# =========================================================

@st.cache_resource
def get_connection():
    """
    Tạo kết nối MySQL tới Aiven.

    Aiven yêu cầu kết nối SSL/TLS.
    ssl_verify_cert=False được sử dụng để không cần
    tải riêng file CA certificate.
    """

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,

            # SSL/TLS cho Aiven
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )

        return conn

    except Exception as e:
        st.error(
            "❌ Không thể kết nối MySQL Aiven."
        )

        st.error(
            f"Chi tiết lỗi: {e}"
        )

        st.stop()


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

def init_db():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,

                    room_number VARCHAR(50)
                        NOT NULL UNIQUE,

                    room_type VARCHAR(100)
                        NOT NULL,

                    floor INT
                        NOT NULL,

                    price DECIMAL(15,2)
                        NOT NULL DEFAULT 0,

                    status VARCHAR(50)
                        NOT NULL DEFAULT 'Trống',

                    customer_name VARCHAR(255)
                        DEFAULT '',

                    phone VARCHAR(50)
                        DEFAULT '',

                    check_in VARCHAR(50)
                        DEFAULT '',

                    check_out VARCHAR(50)
                        DEFAULT '',

                    note TEXT
                )
                ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

        conn.commit()

    except Exception as e:

        conn.rollback()

        st.error(
            f"❌ Không thể tạo bảng rooms: {e}"
        )

        st.stop()


# =========================================================
# LẤY DANH SÁCH PHÒNG
# =========================================================

def load_rooms():

    conn = get_connection()

    try:

        query = """
            SELECT
                id,
                room_number,
                room_type,
                floor,
                price,
                status,
                customer_name,
                phone,
                check_in,
                check_out,
                note
            FROM rooms
            ORDER BY floor, room_number
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as e:

        st.error(
            f"❌ Không thể tải dữ liệu phòng: {e}"
        )

        return pd.DataFrame(
            columns=[
                "id",
                "room_number",
                "room_type",
                "floor",
                "price",
                "status",
                "customer_name",
                "phone",
                "check_in",
                "check_out",
                "note"
            ]
        )


# =========================================================
# THÊM PHÒNG
# =========================================================

def add_room(
    room_number,
    room_type,
    floor,
    price,
    status="Trống"
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO rooms
                (
                    room_number,
                    room_type,
                    floor,
                    price,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                room_number,
                room_type,
                floor,
                price,
                status
            ))

        conn.commit()

        return True, "Thêm phòng thành công!"

    except pymysql.err.IntegrityError:

        conn.rollback()

        return False, "Số phòng đã tồn tại!"

    except Exception as e:

        conn.rollback()

        return False, f"Lỗi database: {e}"


# =========================================================
# CẬP NHẬT PHÒNG
# =========================================================

def update_room(
    room_id,
    room_number,
    room_type,
    floor,
    price,
    status,
    customer_name,
    phone,
    check_in,
    check_out,
    note
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE rooms

                SET
                    room_number = %s,
                    room_type = %s,
                    floor = %s,
                    price = %s,
                    status = %s,
                    customer_name = %s,
                    phone = %s,
                    check_in = %s,
                    check_out = %s,
                    note = %s

                WHERE id = %s
            """, (
                room_number,
                room_type,
                floor,
                price,
                status,
                customer_name,
                phone,
                check_in,
                check_out,
                note,
                room_id
            ))

        conn.commit()

        return True, "Cập nhật phòng thành công!"

    except pymysql.err.IntegrityError:

        conn.rollback()

        return False, "Số phòng đã tồn tại!"

    except Exception as e:

        conn.rollback()

        return False, f"Lỗi database: {e}"


# =========================================================
# XÓA PHÒNG
# =========================================================

def delete_room(room_id):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM rooms
                WHERE id = %s
            """, (room_id,))

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        st.error(
            f"Không thể xóa phòng: {e}"
        )

        return False


# =========================================================
# CẬP NHẬT TRẠNG THÁI
# =========================================================

def update_status(room_id, status):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE rooms
                SET status = %s
                WHERE id = %s
            """, (
                status,
                room_id
            ))

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        st.error(
            f"Không thể cập nhật trạng thái: {e}"
        )

        return False


# =========================================================
# TẠO DỮ LIỆU MẪU
# =========================================================

def create_sample_data():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) AS total FROM rooms"
            )

            result = cursor.fetchone()

            count = result["total"]

            if count == 0:

                sample_rooms = [

                    (
                        "101",
                        "Standard",
                        1,
                        500000,
                        "Trống"
                    ),

                    (
                        "102",
                        "Standard",
                        1,
                        500000,
                        "Đã đặt"
                    ),

                    (
                        "103",
                        "Deluxe",
                        1,
                        750000,
                        "Đang ở"
                    ),

                    (
                        "201",
                        "Deluxe",
                        2,
                        750000,
                        "Trống"
                    ),

                    (
                        "202",
                        "Suite",
                        2,
                        1200000,
                        "Trống"
                    ),

                    (
                        "203",
                        "Suite",
                        2,
                        1200000,
                        "Bảo trì"
                    ),

                    (
                        "301",
                        "Standard",
                        3,
                        500000,
                        "Trống"
                    ),

                    (
                        "302",
                        "Deluxe",
                        3,
                        750000,
                        "Đang ở"
                    )
                ]

                cursor.executemany("""
                    INSERT INTO rooms
                    (
                        room_number,
                        room_type,
                        floor,
                        price,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, sample_rooms)

                conn.commit()

    except Exception as e:

        conn.rollback()

        st.warning(
            f"Không thể tạo dữ liệu mẫu: {e}"
        )


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

init_db()
create_sample_data()


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 15px;
    border-radius: 12px;
}

.room-card {
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    background: white;
    margin-bottom: 10px;
}

.status-empty {
    color: #15803d;
    font-weight: bold;
}

.status-booked {
    color: #ca8a04;
    font-weight: bold;
}

.status-occupied {
    color: #dc2626;
    font-weight: bold;
}

.status-maintenance {
    color: #7c3aed;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏨 HOTEL MANAGER")

st.sidebar.caption(
    "Hệ thống quản lý phòng khách sạn"
)

page = st.sidebar.radio(
    "MENU",
    [
        "📊 Tổng quan",
        "🛏️ Quản lý phòng",
        "➕ Thêm phòng",
        "📋 Đặt phòng / Nhận phòng",
        "⚙️ Cài đặt"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Hotel Management System"
)

st.sidebar.caption(
    "MySQL Aiven Database"
)

st.sidebar.caption(
    "Version 2.0"
)


# =========================================================
# LOAD DATA
# =========================================================

df = load_rooms()


# =========================================================
# TRANG TỔNG QUAN
# =========================================================

if page == "📊 Tổng quan":

    st.title("🏨 Tổng quan khách sạn")

    # Ảnh logo
    try:

        st.image(
            "logo.jpg",
            caption="Vũng Tàu",
            use_container_width=True
        )

    except Exception:

        st.info(
            "💡 Đặt file logo.jpg cùng thư mục với app.py "
            "để hiển thị hình ảnh khách sạn."
        )

    st.caption(
        f"Cập nhật lúc "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    # -----------------------------------------------------
    # THỐNG KÊ
    # -----------------------------------------------------

    total_rooms = len(df)

    empty_rooms = len(
        df[df["status"] == "Trống"]
    )

    booked_rooms = len(
        df[df["status"] == "Đã đặt"]
    )

    occupied_rooms = len(
        df[df["status"] == "Đang ở"]
    )

    maintenance_rooms = len(
        df[df["status"] == "Bảo trì"]
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "🏨 Tổng phòng",
        total_rooms
    )

    col2.metric(
        "🟢 Phòng trống",
        empty_rooms
    )

    col3.metric(
        "🟡 Đã đặt",
        booked_rooms
    )

    col4.metric(
        "🔴 Đang ở",
        occupied_rooms
    )

    col5.metric(
        "🟣 Bảo trì",
        maintenance_rooms
    )

    st.divider()

    # -----------------------------------------------------
    # CÔNG SUẤT PHÒNG
    # -----------------------------------------------------

    if total_rooms > 0:

        occupied_rate = (
            occupied_rooms / total_rooms
        ) * 100

        st.subheader(
            "📈 Tình trạng sử dụng phòng"
        )

        st.progress(
            min(occupied_rate / 100, 1.0)
        )

        st.write(
            f"**Công suất phòng hiện tại: "
            f"{occupied_rate:.1f}%**"
        )

    st.divider()

    # -----------------------------------------------------
    # DANH SÁCH + DOANH THU
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "📋 Danh sách phòng"
        )

        if len(df) > 0:

            display_df = df[
                [
                    "room_number",
                    "room_type",
                    "floor",
                    "price",
                    "status"
                ]
            ].copy()

            display_df.columns = [
                "Phòng",
                "Loại phòng",
                "Tầng",
                "Giá/đêm",
                "Trạng thái"
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có dữ liệu phòng."
            )

    with col2:

        st.subheader(
            "💰 Doanh thu dự kiến"
        )

        occupied_revenue = df[
            df["status"] == "Đang ở"
        ]["price"].sum()

        booked_revenue = df[
            df["status"] == "Đã đặt"
        ]["price"].sum()

        c1, c2 = st.columns(2)

        c1.metric(
            "Đang ở",
            f"{occupied_revenue:,.0f} ₫"
        )

        c2.metric(
            "Đã đặt",
            f"{booked_revenue:,.0f} ₫"
        )


# =========================================================
# QUẢN LÝ PHÒNG
# =========================================================

elif page == "🛏️ Quản lý phòng":

    st.title(
        "🛏️ Quản lý phòng"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "🔎 Tìm phòng",
            placeholder="Nhập số phòng..."
        )

    with col2:

        status_filter = st.selectbox(
            "Trạng thái",
            [
                "Tất cả",
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì"
            ]
        )

    with col3:

        room_types = []

        if len(df) > 0:

            room_types = sorted(
                df["room_type"]
                .dropna()
                .unique()
                .tolist()
            )

        type_filter = st.selectbox(
            "Loại phòng",
            ["Tất cả"] + room_types
        )

    # -----------------------------------------------------
    # FILTER
    # -----------------------------------------------------

    filtered = df.copy()

    if search:

        filtered = filtered[
            filtered["room_number"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    if status_filter != "Tất cả":

        filtered = filtered[
            filtered["status"] == status_filter
        ]

    if type_filter != "Tất cả":

        filtered = filtered[
            filtered["room_type"] == type_filter
        ]

    st.write(
        f"Hiển thị **{len(filtered)}** phòng"
    )

    st.divider()

    # -----------------------------------------------------
    # HIỂN THỊ PHÒNG
    # -----------------------------------------------------

    for _, room in filtered.iterrows():

        status = room["status"]

        if status == "Trống":

            icon = "🟢"

        elif status == "Đã đặt":

            icon = "🟡"

        elif status == "Đang ở":

            icon = "🔴"

        else:

            icon = "🟣"

        with st.expander(
            f"{icon} Phòng "
            f"{room['room_number']} — "
            f"{room['room_type']} — "
            f"{room['price']:,.0f} ₫/đêm"
        ):

            c1, c2, c3 = st.columns(3)

            c1.write(
                f"**Tầng:** {room['floor']}"
            )

            c2.write(
                f"**Loại:** {room['room_type']}"
            )

            c3.write(
                f"**Trạng thái:** {status}"
            )

            if room["customer_name"]:

                st.info(
                    f"👤 Khách: "
                    f"{room['customer_name']}"
                )

            if room["phone"]:

                st.write(
                    f"📞 SĐT: "
                    f"{room['phone']}"
                )

            if room["check_in"]:

                st.write(
                    f"📅 Check-in: "
                    f"{room['check_in']}"
                )

            if room["check_out"]:

                st.write(
                    f"📅 Check-out: "
                    f"{room['check_out']}"
                )

            if room["note"]:

                st.write(
                    f"📝 Ghi chú: "
                    f"{room['note']}"
                )

            st.divider()

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                if st.button(
                    "🟢 Trống",
                    key=f"empty_{room['id']}"
                ):

                    update_status(
                        room["id"],
                        "Trống"
                    )

                    st.rerun()

            with c2:

                if st.button(
                    "🟡 Đã đặt",
                    key=f"booked_{room['id']}"
                ):

                    update_status(
                        room["id"],
                        "Đã đặt"
                    )

                    st.rerun()

            with c3:

                if st.button(
                    "🔴 Đang ở",
                    key=f"occupied_{room['id']}"
                ):

                    update_status(
                        room["id"],
                        "Đang ở"
                    )

                    st.rerun()

            with c4:

                if st.button(
                    "🟣 Bảo trì",
                    key=f"maintenance_{room['id']}"
                ):

                    update_status(
                        room["id"],
                        "Bảo trì"
                    )

                    st.rerun()

            st.divider()

            if st.button(
                "🗑️ Xóa phòng",
                key=f"delete_{room['id']}"
            ):

                if delete_room(room["id"]):

                    st.success(
                        "Đã xóa phòng."
                    )

                    st.rerun()


# =========================================================
# THÊM PHÒNG
# =========================================================

elif page == "➕ Thêm phòng":

    st.title(
        "➕ Thêm phòng mới"
    )

    with st.form(
        "add_room_form"
    ):

        col1, col2 = st.columns(2)

        with col1:

            room_number = st.text_input(
                "Số phòng *",
                placeholder="Ví dụ: 105"
            )

            room_type = st.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Superior",
                    "Deluxe",
                    "Suite",
                    "Family",
                    "VIP"
                ]
            )

            floor = st.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=1,
                step=1
            )

        with col2:

            price = st.number_input(
                "Giá phòng / đêm (VNĐ)",
                min_value=0,
                value=500000,
                step=50000
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Bảo trì"
                ]
            )

        submit = st.form_submit_button(
            "➕ Thêm phòng",
            use_container_width=True
        )

        if submit:

            if not room_number.strip():

                st.error(
                    "Vui lòng nhập số phòng."
                )

            else:

                success, message = add_room(
                    room_number.strip(),
                    room_type,
                    floor,
                    price,
                    status
                )

                if success:

                    st.success(
                        message
                    )

                    st.balloons()

                    st.rerun()

                else:

                    st.error(
                        message
                    )


# =========================================================
# ĐẶT PHÒNG / NHẬN PHÒNG
# =========================================================

elif page == "📋 Đặt phòng / Nhận phòng":

    st.title(
        "📋 Đặt phòng / Nhận phòng"
    )

    available = df[
        df["status"].isin(
            [
                "Trống",
                "Đã đặt",
                "Đang ở"
            ]
        )
    ]

    if len(available) == 0:

        st.warning(
            "Không có phòng khả dụng."
        )

    else:

        room_options = {

            f"Phòng {row.room_number} - "
            f"{row.room_type} - "
            f"{row.status}":

            row.id

            for row in available.itertuples()
        }

        selected_room = st.selectbox(
            "Chọn phòng",
            list(room_options.keys())
        )

        room_id = room_options[
            selected_room
        ]

        room = df[
            df["id"] == room_id
        ].iloc[0]

        st.info(
            f"Phòng **{room['room_number']}** | "
            f"{room['room_type']} | "
            f"{room['price']:,.0f} ₫/đêm"
        )

        with st.form(
            "booking_form"
        ):

            customer_name = st.text_input(
                "👤 Tên khách hàng"
            )

            phone = st.text_input(
                "📞 Số điện thoại"
            )

            col1, col2 = st.columns(2)

            with col1:

                check_in = st.date_input(
                    "📅 Ngày nhận phòng",
                    value=date.today()
                )

            with col2:

                check_out = st.date_input(
                    "📅 Ngày trả phòng",
                    value=date.today()
                )

            new_status = st.selectbox(
                "Trạng thái",
                [
                    "Đã đặt",
                    "Đang ở",
                    "Trống"
                ]
            )

            note = st.text_area(
                "📝 Ghi chú"
            )

            submit = st.form_submit_button(
                "💾 Lưu thông tin",
                use_container_width=True
            )

            if submit:

                if check_out < check_in:

                    st.error(
                        "Ngày trả phòng không được "
                        "trước ngày nhận phòng."
                    )

                else:

                    success, message = update_room(
                        room["id"],
                        room["room_number"],
                        room["room_type"],
                        room["floor"],
                        room["price"],
                        new_status,
                        customer_name,
                        phone,
                        check_in.strftime(
                            "%d/%m/%Y"
                        ),
                        check_out.strftime(
                            "%d/%m/%Y"
                        ),
                        note
                    )

                    if success:

                        st.success(
                            message
                        )

                        st.rerun()

                    else:

                        st.error(
                            message
                        )


# =========================================================
# CÀI ĐẶT
# =========================================================

elif page == "⚙️ Cài đặt":

    st.title(
        "⚙️ Cài đặt"
    )

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    st.subheader(
        "🗄️ Cơ sở dữ liệu"
    )

    st.success(
        "🟢 Đang kết nối MySQL Aiven"
    )

    st.write(
        f"**Host:** `{MYSQL_HOST}`"
    )

    st.write(
        f"**Port:** `{MYSQL_PORT}`"
    )

    st.write(
        f"**Database:** `{MYSQL_DATABASE}`"
    )

    st.write(
        f"**User:** `{MYSQL_USER}`"
    )

    st.write(
        f"Tổng số phòng: **{len(df)}**"
    )

    st.divider()

    # -----------------------------------------------------
    # THỐNG KÊ LOẠI PHÒNG
    # -----------------------------------------------------

    st.subheader(
        "📊 Thống kê"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Theo loại phòng**"
        )

        if len(df) > 0:

            type_stats = (
                df["room_type"]
                .value_counts()
                .reset_index()
            )

            type_stats.columns = [
                "Loại phòng",
                "Số lượng"
            ]

            st.dataframe(
                type_stats,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có dữ liệu."
            )

    with col2:

        st.write(
            "**Theo trạng thái**"
        )

        if len(df) > 0:

            status_stats = (
                df["status"]
                .value_counts()
                .reset_index()
            )

            status_stats.columns = [
                "Trạng thái",
                "Số lượng"
            ]

            st.dataframe(
                status_stats,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có dữ liệu."
            )

    st.divider()

    # -----------------------------------------------------
    # LÀM MỚI
    # -----------------------------------------------------

    st.subheader(
        "🔄 Làm mới dữ liệu"
    )

    if st.button(
        "🔄 Tải lại dữ liệu",
        use_container_width=True
    ):

        st.rerun()

    st.divider()

    st.caption(
        "Hotel Room Manager — "
        "Streamlit + MySQL + Aiven"
    )
