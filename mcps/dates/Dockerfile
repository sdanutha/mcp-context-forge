FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "mcp==1.30.0"
COPY server.py .
USER 10001:10001
EXPOSE 8001
CMD ["python", "server.py"]
