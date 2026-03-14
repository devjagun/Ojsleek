FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gfortran \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN gfortran -o loss_calc loss_calculator.f90

EXPOSE 8081

CMD ["python", "server.py"]
