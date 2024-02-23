FROM python:3.8

# Install dependencies
RUN apt-get update && apt-get install -y \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application files into the container
COPY d_fake_seeder /app

# Install Python dependencies
RUN pip install -r requirements.txt  # If you have a requirements.txt file

# Set environment variable to display GUI on the host
ENV DISPLAY=:0

# Run the Python GTK application
CMD ["python", "dfakeseeder.py"]
