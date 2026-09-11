# CANON Platform — container for a shareable public URL (HF Spaces / Render / Fly / Railway)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# HF Spaces expects 7860; Render/Railway inject $PORT. app.py reads either.
ENV CANON_PLATFORM_PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
