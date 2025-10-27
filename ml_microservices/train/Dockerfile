FROM python:3.12-slim
RUN apt update -y && apt install awscli -y
WORKDIR /app

COPY requirements.txt setup.py README.md /app/

COPY ./src /app/src
# 2. Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 3. Copy the rest of the application code
COPY . /app
# 3. Now, copy the rest of your application source code
ENV PYTHONPATH=/app/src
COPY . .

EXPOSE 3004

# This command assumes your uvicorn entrypoint is in the root of the project.
# You might need to adjust "app:app" if it's inside a subfolder, 
# e.g., "ml_microservices.auth.app:app"
CMD ["uvicorn", "ml_microservices.train.app:app", "--host", "0.0.0.0", "--port", "3004"]
