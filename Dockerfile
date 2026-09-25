FROM python:3.12-slim
WORKDIR /project
RUN apt-get update && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
ENV PYTHONPATH=/project/src
CMD ["make", "reproduce-offline"]
