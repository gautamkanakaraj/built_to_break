FROM python:3.10-alpine

WORKDIR /app

# Install build dependencies for C-extensions if needed
RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 4000 as per requirements
EXPOSE 4000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4000"]
