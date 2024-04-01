FROM python:3.11

# Update
RUN apt-get update  

# Install dependencies
RUN apt-get install -y gtk-4-examples libgtk-4-dev python3-gi python3-gi-cairo python3-requests gir1.2-gtk-4.0

# cleanup
RUN  rm -rf /var/lib/apt/lists/*

# Copy the application files into the container
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Set environment variable to display GUI on the host
ENV DISPLAY=:0

# set working directory
WORKDIR /app/d_fake_seeder

# Set environment variable to include the path
ENV PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH}"

# Run the Python GTK application
CMD ["python3", "dfakeseeder.py"]
