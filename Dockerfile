FROM python:3.11-slim

WORKDIR /app

# تثبيت الاعتماديات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]