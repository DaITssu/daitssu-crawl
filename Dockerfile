FROM python:3.10.12

WORKDIR /app/
COPY ./ /app/

RUN pip install -r requirements.txt

CMD ["python", "lambda_function.py"]
