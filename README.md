\# RFM Repurchase Decision API



API สำหรับแสดงผลการทำนายการซื้อซ้ำ (Repurchase) จาก RFM + CatBoost  

พร้อม Decision Flow ให้ลูกค้าเลือก Reward



---



\## Tech Stack

\- Python

\- Pandas

\- CatBoost (model already trained)

\- FastAPI

\- Uvicorn

\- Docker



---



\## Project Structure





---



\## API Endpoints

\- `GET /health` – API health check

\- `GET /customer/{customer\_id}` – Get customer prediction \& segment

\- `POST /choice` – Save customer decision

\- `GET /choice/latest/{customer\_id}` – Get latest customer choice



---



\## Run with Docker



```bash

docker build -t rfm-api:0.1 .

docker run --rm -p 8000:8000 rfm-api:0.1



\## Example

GET /customer/12346



\## Response

{

&nbsp; "status": "ok",

&nbsp; "Customer\_ID": 12346,

&nbsp; "Segment": "Low",

&nbsp; "Pred\_Repurchase\_Count": 0.48

}



