FROM python:3.11-slim

RUN apt-get update && apt-get install -y gfortran libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY bonus_calc.f90 .
RUN gfortran -O2 -o bonus_calc bonus_calc.f90

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 9000

CMD ["python", "app.py"]
