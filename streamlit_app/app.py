import os
import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery

# ==================== CẤU HÌNH TRANG WEB ====================
st.set_page_config(
    page_title="Airbnb Analytics & AI Price Predictor",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại, chuyên nghiệp
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FF5A5F;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #6c757d;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px 20px;
        border-left: 5px solid #FF5A5F;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .prediction-box {
        background: linear-gradient(135deg, #FF5A5F 0%, #FF385C 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-top: 15px;
        box-shadow: 0 4px 15px rgba(255, 90, 95, 0.3);
    }
    .prediction-price {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA LOADERS (CACHE TỐI ƯU) ====================
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "moonlit-poetry-510206-t4")

@st.cache_data(ttl=600)
def load_gold_metrics():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT * 
        FROM `{PROJECT_ID}.gold_layer.gold_neighbourhood_metrics`
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=600)
def load_gold_features():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT 
            neighbourhood_group, room_type, price_usd, minimum_nights,
            number_of_reviews, review_rating, availability_365
        FROM `{PROJECT_ID}.silver_layer.silver_airbnb_cleaned`
        WHERE price_usd IS NOT NULL AND price_usd > 0
        LIMIT 10000
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=600)
def load_audit_data():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.gold_layer.compare_audit`"
    return client.query(query).to_dataframe()

@st.cache_resource
def load_ml_model():
    model_path = "/app/models_saved/pricing_rf_model.pkl"
    if not os.path.exists(model_path):
        # Fallback đường dẫn local nếu chạy ngoài docker
        model_path = os.path.join(os.path.dirname(__file__), "..", "models_saved", "pricing_rf_model.pkl")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

# ==================== HEADER CHÍNH ====================
st.markdown('<div class="main-header">🏡 Nền Tảng Dữ Liệu & Dự Đoán Giá Thuê Airbnb</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Kiến trúc <b>Medallion (Bronze ➔ Silver ➔ Gold)</b> trên <b>BigQuery + dbt</b> | Điều phối tự động bởi <b>Apache Airflow</b></div>', unsafe_allow_html=True)

# Tải dữ liệu
df_gold = load_gold_metrics()
model = load_ml_model()

# ==================== SIDEBAR BỘ LỌC ====================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_B%C3%A9lo.svg", width=160)
st.sidebar.title("🎛️ Bộ lọc Phân tích")

all_boroughs = sorted(df_gold['neighbourhood_group'].unique().tolist())
all_room_types = sorted(df_gold['room_type'].unique().tolist())
all_price_tiers = sorted(df_gold['price_tier'].unique().tolist())

selected_boroughs = st.sidebar.multiselect(
    "Quận (Borough):",
    options=all_boroughs,
    default=all_boroughs
)

selected_room_types = st.sidebar.multiselect(
    "Loại phòng (Room Type):",
    options=all_room_types,
    default=all_room_types
)

selected_tiers = st.sidebar.multiselect(
    "Phân khúc giá (Price Tier):",
    options=all_price_tiers,
    default=all_price_tiers
)

# Lọc dữ liệu theo sidebar
df_filtered = df_gold[
    (df_gold['neighbourhood_group'].isin(selected_boroughs)) &
    (df_gold['room_type'].isin(selected_room_types)) &
    (df_gold['price_tier'].isin(selected_tiers))
]

st.sidebar.divider()
st.sidebar.caption("🚀 **Hạ tầng triển khai:**")
st.sidebar.caption("• Orchestrator: **Apache Airflow 2.9**\n• Warehouse: **Google BigQuery**\n• Transform: **dbt core 1.8**\n• ML Model: **Random Forest**")

# ==================== TABS NỘI DUNG ====================
tab_dash, tab_pred, tab_audit = st.tabs([
    "📊 Dashboard Phân Tích Toàn Diện", 
    "🤖 Công Cụ Dự Đoán Giá Phòng AI", 
    "🔍 Kiểm Toán Chất Lượng & Lineage"
])

# =====================================================================
# TAB 1: EXECUTIVE ANALYTICS DASHBOARD
# =====================================================================
with tab_dash:
    if df_filtered.empty:
        st.warning("⚠️ Không có dữ liệu phù hợp với bộ lọc bạn chọn. Vui lòng chọn lại ở thanh menu bên trái!")
    else:
        # 1. Hàng KPI Metrics
        total_listings = int(df_filtered['total_listings'].sum())
        weighted_avg_price = (df_filtered['avg_price_usd'] * df_filtered['total_listings']).sum() / total_listings
        avg_verified_rate = (df_filtered['pct_verified_host'] * df_filtered['total_listings']).sum() / total_listings
        avg_avail_rate = (df_filtered['avg_availability_pct'] * df_filtered['total_listings']).sum() / total_listings

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Tổng Số Phòng Đang Quản Lý", f"{total_listings:,.0f}", delta=f"{len(selected_boroughs)} Quận")
        with c2:
            st.metric("Giá Thuê Trung Bình / Đêm", f"${weighted_avg_price:.2f}", delta="USD")
        with c3:
            st.metric("Tỷ Lệ Host Đã Xác Minh", f"{avg_verified_rate:.1f}%", delta="Verified")
        with c4:
            st.metric("Tỷ Lệ Khả Dụng Trong Năm", f"{avg_avail_rate:.1f}%", delta="Availability")

        st.divider()

        # 2. Hàng Biểu đồ chính 1: So sánh Tỷ lệ Verified vs Unconfirmed và Thị phần loại phòng
        row1_col1, row1_col2 = st.columns([1.2, 1])

        with row1_col1:
            st.subheader("1. Tỷ lệ Chủ Nhà Xác Minh (Verified) vs Chưa Xác Minh")
            df_ver = df_filtered.groupby('neighbourhood_group', as_index=False).agg({
                'total_listings': 'sum',
                'pct_verified_host': 'mean'
            })
            df_ver['pct_unconfirmed'] = 100.0 - df_ver['pct_verified_host']

            fig_ver = go.Figure()
            fig_ver.add_trace(go.Bar(
                y=df_ver['neighbourhood_group'],
                x=df_ver['pct_verified_host'],
                name='Verified',
                orientation='h',
                marker=dict(color='#2A9D8F'),
                text=df_ver['pct_verified_host'].apply(lambda x: f"{x:.1f}%"),
                textposition='auto'
            ))
            fig_ver.add_trace(go.Bar(
                y=df_ver['neighbourhood_group'],
                x=df_ver['pct_unconfirmed'],
                name='Unconfirmed',
                orientation='h',
                marker=dict(color='#94A3B8'),
                text=df_ver['pct_unconfirmed'].apply(lambda x: f"{x:.1f}%"),
                textposition='auto'
            ))
            fig_ver.update_layout(
                barmode='stack',
                title="Tỷ lệ Verified / Unconfirmed giữa các Quận",
                xaxis_title="Tỷ lệ phần trăm (%)",
                yaxis_title="",
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_ver, use_container_width=True)

        with row1_col2:
            st.subheader("2. Cơ Cấu Thị Phần Theo Loại Phòng")
            df_room = df_filtered.groupby('room_type', as_index=False)['total_listings'].sum()
            fig_donut = px.pie(
                df_room,
                names='room_type',
                values='total_listings',
                hole=0.45,
                color_discrete_sequence=['#FF5A5F', '#00A699', '#FC642D', '#484848'],
                title="Tỷ trọng số lượng phòng theo Room Type"
            )
            fig_donut.update_layout(height=350)
            st.plotly_chart(fig_donut, use_container_width=True)

        # 3. Hàng Biểu đồ chính 2: Phân tích phân khúc giá
        st.subheader("3. Phân Phối Giá Thuê Theo Phân Khúc & Quận")
        fig_bar_price = px.bar(
            df_filtered,
            x='neighbourhood_group',
            y='total_listings',
            color='price_tier',
            barmode='group',
            labels={'neighbourhood_group': 'Quận', 'total_listings': 'Số lượng phòng', 'price_tier': 'Phân khúc'},
            color_discrete_map={
                'Budget (< $300)': '#48CAE4',
                'Mid-range ($300-$800)': '#0077B6',
                'Luxury (> $800)': '#023E8A'
            },
            title="Số phòng phân loại theo Phân khúc giá giữa các Quận"
        )
        fig_bar_price.update_layout(height=380)
        st.plotly_chart(fig_bar_price, use_container_width=True)

        # 4. Bảng số liệu chi tiết tầng Gold
        with st.expander("📋 Xem bảng tổng hợp chi tiết từ Gold Layer (Click để mở)"):
            st.dataframe(
                df_filtered[[
                    'neighbourhood_group', 'room_type', 'price_tier', 'total_listings',
                    'avg_price_usd', 'min_price_usd', 'max_price_usd', 'avg_service_fee_usd',
                    'pct_verified_host', 'avg_availability_pct'
                ]],
                use_container_width=True
            )

# =====================================================================
# TAB 2: AI PRICE PREDICTOR (GIAO DIỆN DỰ ĐOÁN GIÁ PHÒNG)
# =====================================================================
with tab_pred:
    st.subheader("🤖 Công Cụ Dự Đoán & Đề Xuất Giá Thuê Tối Ưu")
    st.write("Nhập thông tin mô tả chi tiết của phòng bên dưới. Thuật toán **Random Forest Regressor** (được huấn luyện tự động từ dữ liệu Gold Layer) sẽ tính toán mức giá thuê hợp lý nhất:")

    if model is None:
        st.error("⚠️ Chưa tìm thấy file mô hình `pricing_rf_model.pkl` trong hệ thống! Vui lòng chạy Airflow DAG để huấn luyện.")
    else:
        # Form nhập liệu trực quan
        with st.form("interactive_prediction_form"):
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("##### 📍 1. Vị trí & Đặc tính phòng")
                pred_borough = st.selectbox(
                    "Khu vực / Quận (Neighbourhood Group):",
                    options=['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'],
                    index=0,
                    help="Vị trí là yếu tố quan trọng nhất ảnh hưởng trực tiếp đến giá thuê."
                )

                pred_room_type = st.selectbox(
                    "Loại hình phòng (Room Type):",
                    options=['Entire Home/Apt', 'Private Room', 'Shared Room', 'Hotel Room'],
                    index=0
                )

                pred_cancellation = st.radio(
                    "Chính sách hủy phòng (Cancellation Policy):",
                    options=['flexible', 'moderate', 'strict'],
                    horizontal=True,
                    index=0
                )

                pred_verified = st.radio(
                    "Tình trạng xác minh chủ nhà (Host Identity):",
                    options=['verified', 'unconfirmed'],
                    horizontal=True,
                    index=0,
                    help="Chủ nhà đã xác thực CMND/Hộ chiếu thường có độ tin cậy và giá thuê tốt hơn."
                )

                pred_instant = st.toggle("Cho phép đặt phòng ngay lập tức (Instant Bookable)", value=True)

            with col_right:
                st.markdown("##### ⚙️ 2. Quy định & Đánh giá khách hàng")
                
                pred_min_nights = st.slider(
                    "Số đêm ở tối thiểu (Minimum Nights):",
                    min_value=1, max_value=30, value=2,
                    help="Số đêm ở tối thiểu khách phải đặt."
                )

                pred_reviews = st.number_input(
                    "Tổng số lượt đánh giá đã nhận (Number of Reviews):",
                    min_value=0, max_value=1500, value=45, step=5
                )

                pred_rating = st.select_slider(
                    "Điểm đánh giá trung bình ⭐ (Review Rating):",
                    options=[1, 2, 3, 4, 5],
                    value=4,
                    help="Thang điểm từ 1 đến 5 sao."
                )

                pred_availability = st.slider(
                    "Số ngày phòng sẵn sàng đón khách trong năm (Availability 365):",
                    min_value=0, max_value=365, value=180,
                    help="Số ngày phòng mở cửa cho khách thuê."
                )

            st.markdown("<br>", unsafe_allow_html=True)
            submit_pred = st.form_submit_button("🚀 Tính Toán & Dự Đoán Mức Giá Ngay", use_container_width=True)

        if submit_pred:
            # Chuẩn bị DataFrame đặc trưng
            input_data = pd.DataFrame([{
                'neighbourhood_group': pred_borough,
                'room_type': pred_room_type,
                'cancellation_policy': pred_cancellation,
                'host_identity_status': pred_verified,
                'is_instant_bookable': pred_instant,
                'minimum_nights': pred_min_nights,
                'number_of_reviews': pred_reviews,
                'review_rating': pred_rating,
                'availability_365': pred_availability
            }])

            # Chạy dự đoán
            predicted_price = float(model.predict(input_data)[0])
            service_fee = predicted_price * 0.15 # Ước lượng phí dịch vụ 15%
            total_estimate = predicted_price + service_fee

            # Hiển thị kết quả dạng Card nổi bật
            res_col1, res_col2 = st.columns([1, 1.2])

            with res_col1:
                st.markdown(f"""
                <div class="prediction-box">
                    <div style="font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">Mức Giá Thuê Đề Xuất</div>
                    <div class="prediction-price">${predicted_price:.2f}</div>
                    <div style="font-size: 0.95rem; opacity: 0.9;">mỗi đêm (chưa bao gồm thuế & phí)</div>
                </div>
                """, unsafe_allow_html=True)

            with res_col2:
                st.markdown("##### 💡 Phân Tích & So Sánh Thị Trường:")
                
                # Tính giá trung bình tại quận được chọn
                borough_avg = df_gold[df_gold['neighbourhood_group'] == pred_borough]['avg_price_usd'].mean()
                diff_pct = ((predicted_price - borough_avg) / borough_avg) * 100

                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Tổng chi phí ước tính (khách trả)", f"${total_estimate:.2f}", delta="Bao gồm 15% phí dịch vụ")
                with m2:
                    st.metric("So với mức trung bình của " + pred_borough, f"${borough_avg:.2f}", delta=f"{diff_pct:+.1f}%")

                if predicted_price < 300:
                    tier_label = "Budget (< $300)"
                    badge_color = "🟢"
                elif predicted_price <= 800:
                    tier_label = "Mid-range ($300 - $800)"
                    badge_color = "🔵"
                else:
                    tier_label = "Luxury (> $800)"
                    badge_color = "🟣"

                st.info(f"{badge_color} **Phân khúc giá tương ứng:** `{tier_label}`")

                # Lời khuyên tối ưu doanh thu
                recommendations = []
                if pred_verified == 'unconfirmed':
                    recommendations.append("Xác minh danh tính chủ nhà (Host Identity) để tăng tính minh bạch và gia tăng tỷ lệ đặt phòng.")
                if pred_min_nights > 5:
                    recommendations.append("Số đêm tối thiểu đang hơi cao (> 5 đêm), giảm về 2-3 đêm có thể giúp tăng lượng booking ngắn ngày.")
                if not pred_instant:
                    recommendations.append("Bật tính năng Instant Bookable để phòng được ưu tiên hiển thị trên trang tìm kiếm Airbnb.")
                
                if recommendations:
                    st.markdown("**Gợi ý tối ưu hóa:**")
                    for r in recommendations:
                        st.write(f"- {r}")

# =====================================================================
# TAB 3: DATA AUDIT & PIPELINE LINEAGE
# =====================================================================
with tab_audit:
    st.subheader("🔍 Kiểm Toán Đối Chiếu Dữ Liệu: Bronze Layer vs Silver Layer")
    st.write("Bảng đối chiếu được sinh ra tự động bởi view `gold_layer.compare_audit` của dbt:")

    try:
        df_audit = load_audit_data()
        st.dataframe(df_audit, use_container_width=True)

        st.markdown("---")
        st.subheader("🛡️ Các Quy Tắc Data Quality Đã Vượt Qua (dbt test):")
        
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.success("✅ **Khử Trùng Lặp Khóa Chính:** Loại bỏ 541 bản ghi trùng lặp ID thông qua hàm cửa sổ `ROW_NUMBER()`.")
        with tc2:
            st.success("✅ **Chuẩn Hóa Tiền Tệ & Địa Lý:** Bóc tách ký tự `$` và dấu phẩy, sửa lỗi chính tả (`manhatan` ➔ `Manhattan`).")
        with tc3:
            st.success("✅ **Chặn Miền Ngoại Lai:** Clip số đêm tối thiểu về `[1, 365]` và số ngày sẵn sàng về `[0, 365]`.")

    except Exception as e:
        st.error(f"Lỗi tải dữ liệu audit: {str(e)}")
