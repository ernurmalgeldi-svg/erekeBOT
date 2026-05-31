FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY main.py .
EXPOSE 8000
CMD ["python", "main.py"]