FROM python:3.11-slim

# UTF-8 so Persian filenames/pages behave nicely + better logs
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first (faster rebuilds when only code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

EXPOSE 8501

# Run Streamlit (your main entry is خانه.py)
CMD ["streamlit", "run", "خانه.py", "--server.address=0.0.0.0", "--server.port=8501"]
