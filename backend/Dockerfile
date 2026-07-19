# ใช้ Python 3.11 เวอร์ชั่น slim
FROM python:3.11-slim

WORKDIR /app

# คัดลอกไฟล์ requirements.txt เข้าไปก่อนเพื่อติดตั้ง Dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกซอร์สโค้ดทั้งหมดในโฟลเดอร์ backend เข้าไป
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]