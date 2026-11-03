import os
import pandas as pd
from google.cloud import bigquery

def load_csv_to_bronze():
    project_id = os.getenv("GCP_PROJECT_ID", "moonlit-poetry-510206-t4")
    dataset_id = "bronze_layer"
    table_id = "airbnb_raw"
    csv_path = "/opt/airflow/data/Airbnb_Open_Data.csv"
    
    print(f"Bắt đầu đọc file dữ liệu từ: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file: {csv_path}. Hãy kiểm tra thư mục data/.")

    # Đọc dữ liệu dạng thô (low_memory=False để đọc các cột hỗn hợp kiểu)
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Chuẩn hóa tên cột để tránh lỗi ký tự đặc biệt trên BigQuery
    df.columns = [col.strip().replace(" ", "_").replace("-", "_") for col in df.columns]
    
    # Chuyển tất cả cột về kiểu String để bảo toàn dữ liệu thô nguyên bản của tầng Bronze
    df = df.astype(str)
    
    print(f"Tổng số bản ghi đọc được: {len(df)} dòng.")

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, # Ghi đè khi nạp lại
        autodetect=True
    )

    print(f"Đang nạp dữ liệu lên BigQuery bảng: {table_ref}...")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Đợi job hoàn tất

    print(f"Nạp thành công {job.output_rows} dòng vào {table_ref}!")

if __name__ == "__main__":
    load_csv_to_bronze()
