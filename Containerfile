FROM python:3.11-slim

WORKDIR /app

# 複製套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製原始碼並建立資料目錄
COPY src/ ./src/
RUN mkdir -p /app/data

# 設定預設資料庫路徑與環境變數
ENV DB_PATH=/app/data/finance.db
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]