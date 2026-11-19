import io
import uuid
from typing import Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.sale import Sale

# Required columns per project specification
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_name",
    "city",
    "product_name",
    "category",
    "quantity",
    "unit_price",
]

# Smart column aliases to support real-world / retail datasets
COLUMN_ALIASES = {
    "customer_name": [
        "customer_name", "customer", "customer_id", "client_name", "client_id",
        "buyer_name", "customer_full_name", "client",
    ],
    "unit_price": [
        "unit_price", "unit_selling_price_inr", "list_unit_price_inr",
        "unit_selling_price", "selling_price", "price", "unit_cost", "rate",
    ],
    "order_id": ["order_id", "id", "order_number", "transaction_id", "order_no"],
    "order_date": ["order_date", "date", "purchase_date", "transaction_date", "sale_date"],
    "product_name": ["product_name", "product", "item_name", "item", "product_title"],
    "category": ["category", "product_category", "segment", "department"],
    "quantity": ["quantity", "qty", "units", "items", "units_sold"],
    "city": ["city", "location", "town", "customer_city", "region"],
}

# Max file size: 10 MB for MVP safety
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_and_ingest_csv(
    file_bytes: bytes,
    filename: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Parses and validates an uploaded CSV file using Pandas.
    Inserts valid rows into PostgreSQL within a single atomic database transaction.
    """
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum allowed size of 10 MB.")

    if not file_bytes:
        raise ValueError("The uploaded CSV file is empty.")

    # 1. Decode bytes into text
    try:
        content = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("The file could not be decoded. Please upload a standard UTF-8 encoded CSV.")

    # 2. Read with Pandas
    try:
        df = pd.read_csv(io.StringIO(content))
    except Exception as e:
        raise ValueError(f"Failed to parse CSV format: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded CSV file contains no data rows.")

    # Normalize column headers (strip whitespace and lowercase)
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Map column aliases if standard column names are not directly present
    for target_col, aliases in COLUMN_ALIASES.items():
        if target_col not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: target_col})
                    break

    # 3. Check for missing required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_cols)}")

    total_rows = len(df)

    # 4. Data validation and cleaning
    # Clean text columns
    text_cols = ["order_id", "customer_name", "city", "product_name", "category"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    # Drop rows where any required text column is blank or 'nan'
    valid_mask = pd.Series(True, index=df.index)
    for col in text_cols:
        valid_mask &= (df[col] != "") & (df[col].str.lower() != "nan")

    # Validate and convert order_date
    df["order_date_parsed"] = pd.to_datetime(df["order_date"], errors="coerce")
    valid_mask &= df["order_date_parsed"].notna()

    # Validate quantity (must be positive integer)
    df["quantity_parsed"] = pd.to_numeric(df["quantity"], errors="coerce")
    valid_mask &= df["quantity_parsed"].notna() & (df["quantity_parsed"] > 0) & (df["quantity_parsed"] == df["quantity_parsed"].round())

    # Validate unit_price (must be non-negative numeric)
    df["price_parsed"] = pd.to_numeric(df["unit_price"], errors="coerce")
    valid_mask &= df["price_parsed"].notna() & (df["price_parsed"] >= 0)

    # Filter valid vs rejected
    valid_df = df[valid_mask].copy()
    imported_rows = len(valid_df)
    rejected_rows = total_rows - imported_rows

    if imported_rows == 0:
        raise ValueError("No valid rows found. Please check data types, dates, positive quantities, and prices.")

    # 5. Atomic Database Transaction
    dataset_name = filename.rsplit(".", 1)[0]
    dataset = Dataset(
        id=uuid.uuid4(),
        name=dataset_name,
        original_filename=filename,
        row_count=imported_rows,
        status="ready",
    )

    try:
        db.add(dataset)
        # Flush to register dataset.id before creating foreign-keyed sales rows
        db.flush()

        sales_records = [
            Sale(
                dataset_id=dataset.id,
                order_id=row["order_id"],
                order_date=row["order_date_parsed"].date(),
                customer_name=row["customer_name"],
                city=row["city"],
                product_name=row["product_name"],
                category=row["category"],
                quantity=int(row["quantity_parsed"]),
                unit_price=round(float(row["price_parsed"]), 2),
            )
            for _, row in valid_df.iterrows()
        ]

        db.add_all(sales_records)
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database error while saving dataset: {str(e)}")

    return {
        "dataset_id": dataset.id,
        "filename": filename,
        "total_rows": total_rows,
        "imported_rows": imported_rows,
        "rejected_rows": rejected_rows,
        "status": "ready",
    }
