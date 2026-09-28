
import os
import ssl
from datetime import datetime, date

import pandas as pd
import pymysql
import streamlit as st


# =========================================================
# 1. CẤU HÌNH STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Hotel Room Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2. CẤU HÌNH KẾT NỐI AIVEN MYSQL
# =========================================================
# Ưu tiên đọc thông tin từ Streamlit Secrets.
# Không ghi mật khẩu trực tiếp vào mã nguồn.

def get_db_config():
    try:
        secrets = st.secrets

        return {
            "host": secrets["mysql"]["host"],
            "port": int(secrets["mysql"]["port"]),
            "user": secrets["mysql"]["user"],
            "password": secrets["mysql"]["password"],
            "database": secrets["mysql"].get(
                "database", "defaultdb"
            ),
            "ssl_ca": secrets["mysql"].get("ssl_ca", ""),
        }

    except (KeyError, FileNotFoundError):
        # Có thể sử dụng biến môi trường khi chạy ngoài Cloud.
        return {
            "host": os.getenv(
                "MYSQL_HOST",
                "mysql-1cc70107-anhthutran21092005-5a1e.h.aivencloud.com",
            ),
            "port": int(os.getenv("MYSQL_PORT", "12023")),
            "user": os.getenv("MYSQL_USER", "avnadmin"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "defaultdb"),
            "ssl_ca": os.getenv("MYSQL_SSL_CA", ""),
        }


def get_connection():
    config = get_db_config()

    if not config["password"]:
        raise RuntimeError(
            "Chưa cấu hình MYSQL_PASSWORD trong Streamlit Secrets "
            "hoặc biến môi trường."
        )

    # Aiven yêu cầu SSL/TLS.
    # Khuyến nghị cung cấp CA certificate của Aiven để xác minh
    # chứng chỉ máy chủ.
    if config["ssl_ca"]:
        ssl_options = {
            "ca": config["ssl_ca"],
            "check_hostname": True,
        }
    else:
        # Mã hóa kết nối TLS nhưng chưa xác minh danh tính
        # chứng chỉ máy chủ. Nên cấu hình ssl_ca khi triển khai.
        ssl_options = {
            "check_hostname": False,
        }

    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=15,
        read_timeout=30,
        write_timeout=30,
        ssl=ssl_options,
    )


# =========================================================
# 3. KHỞI TẠO BẢNG MYSQL
# =========================================================

def init_db():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT NOT NULL AUTO_INCREMENT,
                    room_number VARCHAR(30) NOT NULL,
                    room_type VARCHAR(50) NOT NULL,
                    floor INT NOT NULL,
                    price DECIMAL(15,2) NOT NULL DEFAULT 0,
                    status VARCHAR(30) NOT NULL DEFAULT 'Trống',
                    customer_name VARCHAR(150) DEFAULT '',
                    phone VARCHAR(30) DEFAULT '',
                    check_in VARCHAR(20) DEFAULT '',
                    check_out VARCHAR(20) DEFAULT '',
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_room_number (room_number)
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# 4. ĐỌC DỮ LIỆU
# =========================================================

def load_rooms():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, room_number, room_type, floor,
                       price, status, customer_name, phone,
                       check_in, check_out, note
                FROM rooms
                ORDER BY floor, room_number
            """)

            rows = cursor.fetchall()

        return pd.DataFrame(
            rows,
            columns=[
                "id", "room_number", "room_type", "floor",
                "price", "status", "customer_name", "phone",
                "check_in", "check_out", "note",
            ],
        )

    finally:
        conn.close()


# =========================================================
# 5. THÊM PHÒNG
# =========================================================

def add_room(
    room_number,
    room_type,
    floor,
    price,
    status="Trống",
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO rooms
                    (room_number, room_type, floor, price, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                room_number,
                room_type,
                int(floor),
                float(price),
                status,
            ))

        conn.commit()
        return True, "Thêm phòng thành công!"

    except pymysql.err.IntegrityError:
        conn.rollback()
        return False, "Số phòng đã tồn tại!"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi thêm phòng: {e}"

    finally:
        conn.close()


# =========================================================
# 6. CẬP NHẬT PHÒNG
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
    note,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE rooms
                SET room_number = %s,
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
                int(floor),
                float(price),
                status,
                customer_name or "",
                phone or "",
                check_in or "",
                check_out or "",
                note or "",
                int(room_id),
            ))

        conn.commit()
        return True, "Cập nhật phòng thành công!"

    except pymysql.err.IntegrityError:
        conn.rollback()
        return False, "Số phòng đã tồn tại!"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi cập nhật: {e}"

    finally:
        conn.close()


# =========================================================
# 7. XÓA PHÒNG
# =========================================================

def delete_room(room_id):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM rooms WHERE id = %s",
                (int(room_id),),
            )

        conn.commit()
        return True, "Đã xóa phòng."

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi xóa phòng: {e}"

    finally:
        conn.close()


# =========================================================
# 8. CẬP NHẬT TRẠNG THÁI
# =========================================================

def update_status(room_id, status):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE rooms
                SET status = %s
                WHERE id = %s
            """, (status, int(room_id)))

        conn.commit()
        return True, "Cập nhật trạng thái thành công!"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi cập nhật trạng thái: {e}"

    finally:
        conn.close()


# =========================================================
# 9. DỮ LIỆU MẪU
# =========================================================

def create_sample_data():
    conn = get_connection()

    sample_rooms = [
        ("101", "Standard", 1, 500000, "Trống"),
        ("102", "Standard", 1, 500000, "Đã đặt"),
        ("103", "Deluxe", 1, 750000, "Đang ở"),
        ("201", "Deluxe", 2, 750000, "Trống"),
        ("202", "Suite", 2, 1200000, "Trống"),
        ("203", "Suite", 2, 1200000, "Bảo trì"),
        ("301", "Standard", 3, 500000, "Trống"),
        ("302", "Deluxe", 3, 750000, "Đang ở"),
    ]

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM rooms")
            count = cursor.fetchone()["total"]

            if count == 0:
                cursor.executemany("""
                    INSERT INTO rooms
                        (room_number, room_type, floor, price, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, sample_rooms)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# 10. KHỞI TẠO DATABASE
# =========================================================

try:
    init_db()
    create_sample_data()

except Exception as e:
    st.error("Không thể kết nối hoặc khởi tạo Aiven MySQL.")
    st.code(str(e))
    st.info(
        "Kiểm tra Host, Port, User, Password, database, "
        "SSL certificate và quyền truy cập của Aiven."
    )
    st.stop()


# =========================================================
# 11. CSS
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
</style>
""", unsafe_allow_html=True)


# =========================================================
# 12. SIDEBAR
# =========================================================

st.sidebar.title("🏨 HOTEL MANAGER")
st.sidebar.caption("Hệ thống quản lý phòng khách sạn")

page = st.sidebar.radio(
    "MENU",
    [
        "📊 Tổng quan",
        "🛏️ Quản lý phòng",
        "➕ Thêm phòng",
        "📋 Đặt phòng / Nhận phòng",
        "⚙️ Cài đặt",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Hotel Management System")
st.sidebar.caption("Database: Aiven MySQL")


# =========================================================
# 13. TẢI DỮ LIỆU
# =========================================================

try:
    df = load_rooms()

except Exception as e:
    st.error("Không thể tải dữ liệu phòng.")
    st.code(str(e))
    st.stop()


# =========================================================
# 14. TỔNG QUAN
# =========================================================

if page == "📊 Tổng quan":

    st.title("🏨 Tổng quan khách sạn")

    # Hiển thị logo nếu file tồn tại.
    if os.path.exists("logo.jpg"):
        st.image(
            "logo.jpg",
            caption="Vũng Tàu",
            use_container_width=True,
        )

    st.caption(
        "Cập nhật lúc "
        + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )

    total_rooms = len(df)
    empty_rooms = int((df["status"] == "Trống").sum())
    booked_rooms = int((df["status"] == "Đã đặt").sum())
    occupied_rooms = int((df["status"] == "Đang ở").sum())
    maintenance_rooms = int((df["status"] == "Bảo trì").sum())

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("🏨 Tổng phòng", total_rooms)
    col2.metric("🟢 Phòng trống", empty_rooms)
    col3.metric("🟡 Đã đặt", booked_rooms)
    col4.metric("🔴 Đang ở", occupied_rooms)
    col5.metric("🟣 Bảo trì", maintenance_rooms)

    st.divider()

    st.subheader("📈 Tình trạng sử dụng phòng")

    if total_rooms > 0:
        occupied_rate = occupied_rooms / total_rooms
        st.progress(occupied_rate)
        st.write(
            f"**Công suất phòng hiện tại: "
            f"{occupied_rate * 100:.1f}%**"
        )
    else:
        st.info("Chưa có dữ liệu phòng.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Danh sách phòng")

        display_df = df[
            ["room_number", "room_type", "floor", "price", "status"]
        ].copy()

        display_df.columns = [
            "Phòng", "Loại phòng", "Tầng", "Giá/đêm", "Trạng thái"
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.subheader("💰 Giá trị phòng theo trạng thái")

        occupied_revenue = df.loc[
            df["status"] == "Đang ở", "price"
        ].sum()

        booked_revenue = df.loc[
            df["status"] == "Đã đặt", "price"
        ].sum()

        c1, c2 = st.columns(2)

        c1.metric("Phòng đang ở", f"{occupied_revenue:,.0f} ₫")
        c2.metric("Phòng đã đặt", f"{booked_revenue:,.0f} ₫")

        st.caption(
            "Đây là tổng giá một đêm của các phòng theo trạng thái, "
            "không phải doanh thu thực thu."
        )


# =========================================================
# 15. QUẢN LÝ PHÒNG
# =========================================================

elif page == "🛏️ Quản lý phòng":

    st.title("🛏️ Quản lý phòng")

    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input(
            "🔎 Tìm phòng",
            placeholder="Nhập số phòng...",
        )

    with col2:
        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả", "Trống", "Đã đặt", "Đang ở", "Bảo trì"],
        )

    with col3:
        room_types = (
            sorted(df["room_type"].dropna().unique().tolist())
            if not df.empty else []
        )

        type_filter = st.selectbox(
            "Loại phòng",
            ["Tất cả"] + room_types,
        )

    filtered = df.copy()

    if search:
        filtered = filtered[
            filtered["room_number"].astype(str).str.contains(
                search, case=False, na=False
            )
        ]

    if status_filter != "Tất cả":
        filtered = filtered[filtered["status"] == status_filter]

    if type_filter != "Tất cả":
        filtered = filtered[filtered["room_type"] == type_filter]

    st.write(f"Hiển thị **{len(filtered)}** phòng")
    st.divider()

    if filtered.empty:
        st.info("Không tìm thấy phòng phù hợp.")

    for _, room in filtered.iterrows():

        status = room["status"]

        icon = {
            "Trống": "🟢",
            "Đã đặt": "🟡",
            "Đang ở": "🔴",
            "Bảo trì": "🟣",
        }.get(status, "⚪")

        with st.expander(
            f"{icon} Phòng {room['room_number']} — "
            f"{room['room_type']} — "
            f"{float(room['price']):,.0f} ₫/đêm"
        ):

            c1, c2, c3 = st.columns(3)

            c1.write(f"**Tầng:** {room['floor']}")
            c2.write(f"**Loại:** {room['room_type']}")
            c3.write(f"**Trạng thái:** {status}")

            if room["customer_name"]:
                st.info(f"👤 Khách: {room['customer_name']}")

            if room["phone"]:
                st.write(f"📞 SĐT: {room['phone']}")

            if room["check_in"]:
                st.write(f"📅 Check-in: {room['check_in']}")

            if room["check_out"]:
                st.write(f"📅 Check-out: {room['check_out']}")

            if room["note"]:
                st.write(f"📝 Ghi chú: {room['note']}")

            st.divider()

            c1, c2, c3, c4 = st.columns(4)

            status_buttons = [
                (c1, "🟢 Trống", "Trống", "empty"),
                (c2, "🟡 Đã đặt", "Đã đặt", "booked"),
                (c3, "🔴 Đang ở", "Đang ở", "occupied"),
                (c4, "🟣 Bảo trì", "Bảo trì", "maintenance"),
            ]

            for col, label, new_status, key_suffix in status_buttons:
                with col:
                    if st.button(
                        label,
                        key=f"{key_suffix}_{room['id']}",
                        use_container_width=True,
                    ):
                        ok, message = update_status(
                            room["id"], new_status
                        )

                        if ok:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            st.divider()

            with st.expander(
                f"✏️ Chỉnh sửa phòng {room['room_number']}"
            ):
                with st.form(f"edit_room_{room['id']}"):

                    edit_number = st.text_input(
                        "Số phòng",
                        value=str(room["room_number"]),
                    )

                    edit_type = st.selectbox(
                        "Loại phòng",
                        [
                            "Standard", "Superior", "Deluxe",
                            "Suite", "Family", "VIP",
                        ],
                        index=(
                            [
                                "Standard", "Superior", "Deluxe",
                                "Suite", "Family", "VIP",
                            ].index(room["room_type"])
                            if room["room_type"] in [
                                "Standard", "Superior", "Deluxe",
                                "Suite", "Family", "VIP",
                            ] else 0
                        ),
                    )

                    edit_floor = st.number_input(
                        "Tầng",
                        min_value=1,
                        max_value=100,
                        value=int(room["floor"]),
                    )

                    edit_price = st.number_input(
                        "Giá phòng/đêm",
                        min_value=0,
                        value=int(float(room["price"])),
                        step=50000,
                    )

                    edit_status = st.selectbox(
                        "Trạng thái",
                        ["Trống", "Đã đặt", "Đang ở", "Bảo trì"],
                        index=(
                            ["Trống", "Đã đặt", "Đang ở", "Bảo trì"].index(status)
                            if status in ["Trống", "Đã đặt", "Đang ở", "Bảo trì"]
                            else 0
                        ),
                    )

                    edit_submit = st.form_submit_button(
                        "💾 Lưu thay đổi",
                        use_container_width=True,
                    )

                    if edit_submit:
                        ok, message = update_room(
                            room["id"],
                            edit_number.strip(),
                            edit_type,
                            edit_floor,
                            edit_price,
                            edit_status,
                            room["customer_name"] or "",
                            room["phone"] or "",
                            room["check_in"] or "",
                            room["check_out"] or "",
                            room["note"] or "",
                        )

                        if ok:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            if st.button(
                "🗑️ Xóa phòng",
                key=f"delete_{room['id']}",
            ):
                ok, message = delete_room(room["id"])

                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


# =========================================================
# 16. THÊM PHÒNG
# =========================================================

elif page == "➕ Thêm phòng":

    st.title("➕ Thêm phòng mới")

    with st.form("add_room_form"):

        col1, col2 = st.columns(2)

        with col1:
            room_number = st.text_input(
                "Số phòng *",
                placeholder="Ví dụ: 105",
            )

            room_type = st.selectbox(
                "Loại phòng",
                ["Standard", "Superior", "Deluxe", "Suite", "Family", "VIP"],
            )

            floor = st.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=1,
                step=1,
            )

        with col2:
            price = st.number_input(
                "Giá phòng / đêm (VNĐ)",
                min_value=0,
                value=500000,
                step=50000,
            )

            status = st.selectbox(
                "Trạng thái",
                ["Trống", "Đã đặt", "Đang ở", "Bảo trì"],
            )

        submit = st.form_submit_button(
            "➕ Thêm phòng",
            use_container_width=True,
        )

        if submit:
            if not room_number.strip():
                st.error("Vui lòng nhập số phòng.")
            else:
                ok, message = add_room(
                    room_number.strip(),
                    room_type,
                    floor,
                    price,
                    status,
                )

                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


# =========================================================
# 17. ĐẶT PHÒNG / NHẬN PHÒNG / TRẢ PHÒNG
# =========================================================

elif page == "📋 Đặt phòng / Nhận phòng":

    st.title("📋 Đặt phòng / Nhận phòng")

    if df.empty:
        st.warning("Chưa có phòng. Hãy thêm phòng trước.")

    else:
        room_options = {
            f"Phòng {row['room_number']} - "
            f"{row['room_type']} - {row['status']}": row["id"]
            for _, row in df[
                df["status"] != "Bảo trì"
            ].iterrows()
        }

        if not room_options:
            st.warning("Không có phòng khả dụng.")
        else:
            selected_room = st.selectbox(
                "Chọn phòng",
                list(room_options.keys()),
            )

            room_id = room_options[selected_room]
            room = df[df["id"] == room_id].iloc[0]

            st.info(
                f"Phòng **{room['room_number']}** | "
                f"{room['room_type']} | "
                f"{float(room['price']):,.0f} ₫/đêm"
            )

            with st.form("booking_form"):

                customer_name = st.text_input(
                    "👤 Tên khách hàng",
                    value=room["customer_name"] or "",
                )

                phone = st.text_input(
                    "📞 Số điện thoại",
                    value=room["phone"] or "",
                )

                def parse_date(value, default):
                    try:
                        return datetime.strptime(
                            str(value), "%d/%m/%Y"
                        ).date()
                    except (ValueError, TypeError):
                        return default

                check_in = st.date_input(
                    "📅 Ngày nhận phòng",
                    value=parse_date(
                        room["check_in"], date.today()
                    ),
                )

                check_out = st.date_input(
                    "📅 Ngày trả phòng",
                    value=parse_date(
                        room["check_out"], date.today()
                    ),
                )

                new_status = st.selectbox(
                    "Trạng thái",
                    ["Đã đặt", "Đang ở", "Trống"],
                    index=(
                        ["Đã đặt", "Đang ở", "Trống"].index(room["status"])
                        if room["status"] in ["Đã đặt", "Đang ở", "Trống"]
                        else 0
                    ),
                )

                note = st.text_area(
                    "📝 Ghi chú",
                    value=room["note"] or "",
                )

                submit = st.form_submit_button(
                    "💾 Lưu thông tin",
                    use_container_width=True,
                )

                if submit:
                    if not customer_name.strip() and new_status != "Trống":
                        st.error("Vui lòng nhập tên khách hàng.")

                    elif check_out < check_in:
                        st.error(
                            "Ngày trả phòng không được trước "
                            "ngày nhận phòng."
                        )

                    else:
                        # Khi trả phòng, có thể chọn Trống.
                        # Xóa thông tin khách để sẵn sàng cho lượt tiếp theo.
                        if new_status == "Trống":
                            customer_name = ""
                            phone = ""
                            check_in_text = ""
                            check_out_text = ""
                            note = ""
                        else:
                            check_in_text = check_in.strftime("%d/%m/%Y")
                            check_out_text = check_out.strftime("%d/%m/%Y")

                        ok, message = update_room(
                            room["id"],
                            room["room_number"],
                            room["room_type"],
                            room["floor"],
                            room["price"],
                            new_status,
                            customer_name,
                            phone,
                            check_in_text,
                            check_out_text,
                            note,
                        )

                        if ok:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)


# =========================================================
# 18. CÀI ĐẶT
# =========================================================

elif page == "⚙️ Cài đặt":

    st.title("⚙️ Cài đặt")

    st.subheader("🗄️ Cơ sở dữ liệu")

    config = get_db_config()

    st.write("**Nhà cung cấp:** Aiven MySQL")
    st.write(f"**Host:** `{config['host']}`")
    st.write(f"**Port:** `{config['port']}`")
    st.write(f"**Database:** `{config['database']}`")
    st.write(f"**User:** `{config['user']}`")
    st.write("**Kết nối:** SSL/TLS")

    st.write(f"Tổng số phòng: **{len(df)}**")

    st.divider()

    st.subheader("📊 Thống kê theo loại phòng")

    if not df.empty:
        type_stats = (
            df["room_type"]
            .value_counts()
            .rename_axis("Loại phòng")
            .reset_index(name="Số lượng")
        )

        st.dataframe(
            type_stats,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("📊 Thống kê theo trạng thái")

        status_stats = (
            df["status"]
            .value_counts()
            .rename_axis("Trạng thái")
            .reset_index(name="Số lượng")
        )

        st.dataframe(
            status_stats,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Chưa có dữ liệu để thống kê.")

    st.divider()

    if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
        st.rerun()

    st.caption("Hotel Room Manager — Streamlit + Aiven MySQL")
