FROM python:3.10

# Install required system dependencies
RUN apt update && apt install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    nano
    # && apt-get clean \
    # && rm -rf /var/lib/apt/lists/*


RUN ./install-miniforge.sh
WORKDIR /app

# Install mt5linux and other dependencies
RUN pip install --upgrade pip
RUN pip install mt5linux

# Add your Python script that will connect to MT5
COPY /scripts/ /app/scripts/
# Set environment variable for MT5 connection

# Run your script
# RUN python ./scripts/example_mt5.py
CMD ["tail", "-f", "/dev/null"]