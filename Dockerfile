FROM python:3.10 AS builder
# COPY requirements.txt .
# COPY . .
WORKDIR /app/
COPY ./ /app/
RUN pip install -r requirements.txt
CMD ["python", "server.py"]

# FROM python:3.10 AS builder
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .3
#
# FROM python:3.10-slim
# COPY --from=builder /app /app
# CMD ["python", "server.py"]
