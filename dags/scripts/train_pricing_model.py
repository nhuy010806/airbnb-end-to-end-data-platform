import os
import joblib
import pandas as pd
from google.cloud import bigquery
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

def train_and_save_model():
    project_id = os.getenv("GCP_PROJECT_ID", "moonlit-poetry-510206-t4")
    if not project_id:
        raise ValueError("Chưa thiết lập biến môi trường GCP_PROJECT_ID!")

    client = bigquery.Client(project=project_id)

    dataset_name = "gold_layer"
    table_name = "gold_ml_features_pricing"
    full_table_id = f"{project_id}.{dataset_name}.{table_name}"
    
    print(f"--> [INFO] Đang truy vấn dữ liệu từ {full_table_id}...")

    query = f"""
        SELECT 
            neighbourhood_group, room_type, cancellation_policy,
            host_identity_status, is_instant_bookable,
            minimum_nights, number_of_reviews, review_rating,
            availability_365, target_price_usd
        FROM `{full_table_id}`
        WHERE target_price_usd IS NOT NULL AND target_price_usd > 0
        LIMIT 50000
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        raise ValueError(f"Bảng {full_table_id} không có dữ liệu để huấn luyện!")

    print(f"--> [INFO] Đã lấy thành công {len(df)} dòng dữ liệu. Bắt đầu tiền xử lý...")

    X = df.drop(columns=['target_price_usd'])
    y = df['target_price_usd']

    categorical_cols = ['neighbourhood_group', 'room_type', 'cancellation_policy', 'host_identity_status']
    numeric_cols = ['minimum_nights', 'number_of_reviews', 'review_rating', 'availability_365']
    bool_cols = ['is_instant_bookable']

    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_cols),
        ('cat', categorical_transformer, categorical_cols),
        ('bool', 'passthrough', bool_cols)
    ])

    model_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=80, max_depth=10, random_state=42, n_jobs=-1))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("--> [INFO] Đang huấn luyện Random Forest...")
    model_pipeline.fit(X_train, y_train)

    score = model_pipeline.score(X_test, y_test)
    print(f"--> [SUCCESS] R^2 Score trên tập Test: {score:.4f}")

    out_dir = "/opt/airflow/models_saved"
    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, "pricing_rf_model.pkl")
    
    joblib.dump(model_pipeline, model_path)
    print(f"=== [HOÀN TẤT] Model đã được lưu tại: {model_path} ===")

if __name__ == "__main__":
    train_and_save_model()
