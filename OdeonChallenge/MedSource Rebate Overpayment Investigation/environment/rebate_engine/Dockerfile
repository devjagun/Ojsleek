FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gnat \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rebate_calc.adb .
RUN gnatmake -O2 rebate_calc.adb -o rebate_calc

COPY app.py .

EXPOSE 5001

CMD ["python", "app.py"]
