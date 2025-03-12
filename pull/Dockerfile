FROM python:3.10

# Install required system dependencies
RUN apt update && apt install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    nano

WORKDIR /app
COPY . .
# Install mt5linux and other dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install mt5linux
RUN pip install pandas


CMD ["tail", "-f", "/dev/null"]