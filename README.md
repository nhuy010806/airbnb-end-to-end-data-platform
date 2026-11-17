# 🏡 Airbnb End-to-End Modern Data & AI Platform

Một giải pháp kỹ thuật dữ liệu (**Data Engineering**) kết hợp trí tuệ nhân tạo (**Machine Learning**) toàn diện, xử lý và phân tích tập dữ liệu phòng thuê Airbnb New York theo kiến trúc chuẩn doanh nghiệp **Medallion Architecture**.

---

## 📌 Mục Lục
1. [Tổng Quan Dự Án](#-tổng-quan-dự-án)
2. [Kiến Trúc Hệ Thống (Architecture)](#-kiến-trúc-hệ-thống-architecture)
3. [Công Nghệ Sử Dụng (Tech Stack)](#-công-nghệ-sử-dụng-tech-stack)
4. [Cấu Trúc Thư Mục (Project Structure)](#-cấu-trúc-thư-mục-project-structure)
5. [Quy Trình Dữ Liệu (Medallion Data Pipeline)](#-quy-trình-dữ-liệu-medallion-data-pipeline)
6. [Mô Hình Học Máy (Machine Learning)](#-mô-hình-học-máy-machine-learning)
7. [Hướng Dẫn Cài Đặt & Khởi Chạy](#-hướng-dẫn-cài-đặt--khởi-chạy)
8. [Các Cổng Truy Cập Dịch Vụ](#-các-cổng-truy-cập-dịch-vụ)

---

## 🎯 Tổng Quan Dự Án

Dự án mô phỏng một Data Platform thực tế trong doanh nghiệp:
- **Tự động hóa luồng dữ liệu (ELT/ETL):** Điều phối nạp dữ liệu từ tệp CSV thô lên Cloud Data Warehouse (Google BigQuery).
- **Chuyển đổi dữ liệu chuẩn Medallion:** Sử dụng **dbt** để xây dựng các tầng dữ liệu **Bronze ➔ Silver ➔ Gold** kèm kiểm thử chất lượng dữ liệu (Data Quality Tests).
- **Mô hình AI dự đoán giá thuê (Price Predictor):** Tự động huấn luyện mô hình **Random Forest** từ dữ liệu tầng Gold và lưu vết mô hình.
- **Ứng dụng Dashboard & Demo trực quan:** Xây dựng Web App tương tác bằng **Streamlit** cho phép người dùng khám phá dữ liệu thị trường và nhập thông số phòng để dự đoán giá thuê theo thời gian thực.

---

## 🏗 Kiến Trúc Hệ Thống (Architecture)

```text
[ Data Source ]
  Airbnb_Open_Data.csv
          │
          ▼ (Task 1: ingest_bronze.py)
┌────────────────────────────────────────────────────────┐
│               GOOGLE CLOUD BIGQUERY                    │
│                                                        │
│   ┌────────────────┐                                   │
│   │  Bronze Layer  │ (Dữ liệu thô nguyên bản)          │
│   └───────┬────────┘                                   │
│           │                                            │
│           ▼ (Task 2: dbt run - silver models)          │
│   ┌────────────────┐                                   │
│   │  Silver Layer  │ (Làm sạch, khử trùng, chuẩn hóa)  │
│   └───────┬────────┘                                   │
│           │                                            │
│           ▼ (Task 2: dbt run - gold models)            │
│   ┌────────────────────────────────────────────────┐   │
│   │                  Gold Layer                    │   │
│   │  - gold_neighbourhood_metrics (Analytics KPI)  │   │
│   │  - gold_ml_features_pricing   (Feature Store)  │   │
│   │  - compare_audit              (Data Quality)   │   │
│   └───────┬────────────────────────────────────────┘   │
└───────────┼────────────────────────────────────────────┘
            │
            ├──────────────────────────┐
            ▼ (Task 4: train_model)    ▼ (Query analytics)
┌────────────────────────┐   ┌────────────────────────┐
│  Scikit-Learn Training │   │     Streamlit App      │
│  (pricing_rf_model.pkl)│──►│  - Analytics Dashboard │
└────────────────────────┘   │  - AI Price Predictor  │
                             └────────────────────────┘
```

---

## 💻 Công Nghệ Sử Dụng (Tech Stack)

| Thành Phần | Công Nghệ | Vai Trò |
| :--- | :--- | :--- |
| **Orchestration** | Apache Airflow 2.x | Lập lịch, điều phối luồng thực thi dữ liệu tự động |
| **Data Warehouse** | Google Cloud BigQuery | Lưu trữ và xử lý truy vấn dữ liệu quy mô lớn |
| **Data Transformation** | dbt (data build tool) | Quản lý biến đổi dữ liệu SQL theo mô hình hóa chuẩn |
| **Machine Learning** | Scikit-learn, Joblib | Tiền xử lý, huấn luyện và lưu trữ mô hình Random Forest |
| **Interactive UI** | Streamlit, Plotly | Giao diện bảng điều khiển phân tích và công cụ dự đoán giá |
| **Containerization** | Docker, Docker Compose | Đóng gói môi trường toàn bộ hệ thống (Airflow, Postgres, Streamlit) |

---

## 📂 Cấu Trúc Thư Mục (Project Structure)

```text
airbnb-data-platform/
│
├── credentials/                 # Khóa bảo mật dịch vụ Google Cloud
│   └── gcp_service_account.json
│
├── data/                        # Tệp dữ liệu đầu vào
│   └── Airbnb_Open_Data.csv
│
├── dags/                        # Mã nguồn Apache Airflow
│   ├── dag_airbnb_medallion_pipeline.py  # DAG điều phối chính
│   └── scripts/
│       ├── ingest_bronze.py             # Script nạp CSV vào BigQuery Bronze
│       └── train_pricing_model.py       # Script train model Scikit-learn
│
├── dbt_project/                 # Dự án biến đổi dữ liệu dbt
│   ├── dbt_project.yml          # Cấu hình project dbt
│   ├── profiles.yml             # Cấu hình kết nối BigQuery
│   └── models/
│       ├── silver/
│       │   ├── schema.yml               # Kiểm thử chất lượng (unique, not_null)
│       │   └── silver_airbnb_cleaned.sql
│       └── gold/
│           ├── compare_audit.sql
│           ├── gold_ml_features_pricing.sql
│           └── gold_neighbourhood_metrics.sql
│
├── models_saved/                # Nơi lưu trữ mô hình AI sau khi huấn luyện
│   └── pricing_rf_model.pkl
│
├── streamlit_app/               # Giao diện Web Application
│   ├── app.py                   # Ứng dụng Streamlit hiển thị và dự đoán
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml           # Khởi chạy đa dịch vụ (Airflow, Postgres, Streamlit)
├── Dockerfile.airflow           # Dockerfile tùy chỉnh cho Airflow (cài dbt, gcp SDK)
└── README.md
```

---

## 🔄 Quy Trình Dữ Liệu (Medallion Data Pipeline)

Pipeline được Apache Airflow tự động thực thi qua 4 giai đoạn tuần tự:

1. **Ingest Bronze Layer (`ingest_bronze_layer`):**
   - Đọc dữ liệu thô từ file `Airbnb_Open_Data.csv`.
   - Chuẩn hóa tên cột, giữ nguyên định dạng kiểu chuỗi để bảo toàn nguyên trạng dữ liệu gốc.
   - Nạp vào bảng `bronze_layer.airbnb_raw` trên BigQuery.

2. **Transform Data (`dbt_run_models`):**
   - **Silver Layer (`silver_airbnb_cleaned`):** Xử lý giá trị rỗng (Null values), ép kiểu dữ liệu chuẩn, chuẩn hóa tiền tệ sang `price_usd`, lọc bỏ các giá trị dị biệt.
   - **Gold Layer:**
     - `gold_neighbourhood_metrics`: Tổng hợp KPI phân tích theo từng quận, loại phòng.
     - `gold_ml_features_pricing`: Lựa chọn các trường đặc trưng quan trọng cho bài toán định giá.
     - `compare_audit`: Bảng thống kê đối soát số lượng bản ghi giữa Bronze và Silver để theo dõi tỷ lệ dữ liệu hợp lệ.

3. **Data Quality Tests (`dbt_test_models`):**
   - Kiểm tra các ràng buộc toàn vẹn dữ liệu: `unique` trên ID phòng, `not_null` trên các trường định danh và trường giá.

4. **Model Training (`train_pricing_ml_model`):**
   - Truy vấn 50.000 mẫu đặc trưng từ bảng `gold_ml_features_pricing`.
   - Xây dựng quy trình tiền xử lý qua `Pipeline` và `ColumnTransformer`:
     - Biến phân loại (Quận, Loại phòng, Chính sách hủy,...): `SimpleImputer` + `OneHotEncoder`.
     - Biến số (Số đêm tối thiểu, Số lượt đánh giá, Điểm review,...): `SimpleImputer` + `StandardScaler`.
   - Huấn luyện thuật toán **RandomForestRegressor** (80 cây quyết định).
   - Xuất file mô hình ra thư mục `models_saved/pricing_rf_model.pkl`.

---

## 🤖 Mô Hình Học Máy (Machine Learning)

- **Bài toán:** Hồi quy dự đoán giá phòng thuê mỗi đêm (USD).
- **Thuật toán:** Random Forest Regressor.
- **Đặc trưng đầu vào (Features):**
  - Vị trí địa lý: `neighbourhood_group` (Manhattan, Brooklyn, Queens, Bronx, Staten Island).
  - Đặc tính phòng: `room_type`, `minimum_nights`, `availability_365`.
  - Uy tín & Chính sách: `cancellation_policy`, `host_identity_status`, `is_instant_bookable`.
  - Phản hồi khách hàng: `number_of_reviews`, `review_rating`.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### Yêu Cầu Tiên Quyết
- Đã cài đặt **Docker Desktop** (bật hỗ trợ WSL 2 trên Windows).
- Đã có tài khoản **Google Cloud Platform (GCP)** và tạo file Service Account JSON cấp quyền truy cập BigQuery lưu tại: `credentials/gcp_service_account.json`.

### Các Bước Khởi Chạy

**Bước 1: Khởi động toàn bộ nền tảng bằng Docker Compose**
```powershell
docker compose up -d
```

**Bước 2: Kích hoạt Pipeline trên Airflow**
1. Truy cập giao diện Airflow Webserver tại: `http://localhost:8082` (Tài khoản: `admin` / `admin`).
2. Tìm DAG có tên: **`dag_airbnb_medallion_pipeline`**.
3. Bật nút **Unpause** và nhấn biểu tượng **Trigger DAG** (Nút Play) để chạy toàn bộ luồng từ Bronze ➔ Silver ➔ Gold ➔ Train AI.

**Bước 3: Trải nghiệm Dashboard và Dự đoán giá trên Streamlit**
1. Mở trình duyệt tại: `http://localhost:8501`.
2. Khám phá biểu đồ phân tích thị trường Airbnb New York.
3. Chuyển sang mục **"Dự Đoán Giá Thuê AI"**, chọn các thông số phòng mong muốn và bấm **"Dự Đoán Giá Thuê Ngay"**.

---

## 🌐 Các Cổng Truy Cập Dịch Vụ

| Dịch Vụ | Địa Chỉ Truy Cập | Thông Tin Đăng Nhập |
| :--- | :--- | :--- |
| **Streamlit Web App** | [http://localhost:8501](http://localhost:8501) | Không yêu cầu |
| **Airflow Webserver** | [http://localhost:8082](http://localhost:8082) | `admin` / `admin` |
| **PostgreSQL Metadata**| `localhost:5432` | `airflow` / `airflow` |

---
⭐ *Dự án được xây dựng phục vụ cho mục đích nghiên cứu, học tập và triển khai kiến trúc dữ liệu hiện đại.*
