from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

app = FastAPI(title="RFM Repurchase Decision API", version="0.1")

# --- paths (อยู่โฟลเดอร์ api/) ---
BASE_DIR = Path(__file__).resolve().parents[1]  # .../api
DF_UI_PATH = BASE_DIR / "df_ui.csv"
CHOICE_LOG_PATH = BASE_DIR / "choice_log.csv"

# --- load data ---
df_ui = None

def load_df_ui():
    global df_ui
    if not DF_UI_PATH.exists():
        raise FileNotFoundError(f"Missing file: {DF_UI_PATH}")
    df = pd.read_csv(DF_UI_PATH)

    # normalize column name
    if "Customer ID" in df.columns and "Customer_ID" not in df.columns:
        df = df.rename(columns={"Customer ID": "Customer_ID"})

    if "Customer_ID" not in df.columns:
        raise ValueError("df_ui.csv must contain column 'Customer_ID' (or 'Customer ID').")

    # set index for fast lookup
    df["Customer_ID"] = pd.to_numeric(df["Customer_ID"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Customer_ID"])
    df["Customer_ID"] = df["Customer_ID"].astype(int)

    df_ui = df.set_index("Customer_ID", drop=False)

def ensure_choice_log():
    if not CHOICE_LOG_PATH.exists():
        pd.DataFrame(columns=["Customer_ID", "Segment", "Selected_Option", "Pred_Repurchase_Count"]).to_csv(
            CHOICE_LOG_PATH, index=False
        )

def available_options(segment: str):
    if segment == "High":
        return ["Cashback", "Gift", "Lucky Draw", "Save Points"]
    elif segment == "Medium":
        return ["Lucky Draw", "Gift", "Save Points"]
    else:
        return ["Save Points", "Lucky Draw"]

@app.on_event("startup")
def startup():
    load_df_ui()
    ensure_choice_log()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/customer/{customer_id}")
def get_customer(customer_id: int):
    if df_ui is None:
        raise HTTPException(status_code=500, detail="df_ui not loaded")

    if customer_id not in df_ui.index:
        raise HTTPException(status_code=404, detail="Customer_ID not found")

    row = df_ui.loc[customer_id]
    seg = str(row.get("Segment", "Low"))
    pred = float(row.get("Pred_Repurchase_Count", 0.0))

    return {
        "status": "ok",
        "Customer_ID": int(customer_id),
        "Segment": seg,
        "Pred_Repurchase_Count": pred,
        "Options": available_options(seg),
    }

class ChoiceIn(BaseModel):
    customer_id: int
    selected_option: str

@app.post("/choice")
def save_choice(payload: ChoiceIn):
    customer_id = int(payload.customer_id)

    if df_ui is None or customer_id not in df_ui.index:
        raise HTTPException(status_code=404, detail="Customer_ID not found")

    row = df_ui.loc[customer_id]
    seg = str(row.get("Segment", "Low"))
    pred = float(row.get("Pred_Repurchase_Count", 0.0))

    opts = available_options(seg)
    if payload.selected_option not in opts:
        raise HTTPException(status_code=400, detail=f"Invalid option for segment '{seg}'. Allowed: {opts}")

    ensure_choice_log()
    log = pd.read_csv(CHOICE_LOG_PATH)

    # keep latest only per customer
    log = log[log["Customer_ID"] != customer_id].copy()

    new_row = pd.DataFrame([{
        "Customer_ID": customer_id,
        "Segment": seg,
        "Selected_Option": payload.selected_option,
        "Pred_Repurchase_Count": pred,
    }])

    log = pd.concat([log, new_row], ignore_index=True)
    log.to_csv(CHOICE_LOG_PATH, index=False)

    return {"status": "saved"}

@app.get("/choice/latest/{customer_id}")
def get_latest_choice(customer_id: int):
    customer_id = int(customer_id)
    if not CHOICE_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="No choices yet")

    log = pd.read_csv(CHOICE_LOG_PATH)
    row = log[log["Customer_ID"] == customer_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="No choice for this customer_id")

    return row.tail(1).to_dict(orient="records")[0]
