# Use the Ubuntu image as a base image
FROM ubuntu:22.04

# Pyodbc exception workaround
RUN apt-get update && apt-get install -y gcc unixodbc-dev python3 python3-pip

# Set the working directory in the container
WORKDIR /app

# Copy the application code and requirements file into the container
COPY app.py requirements.txt /app/

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the port on which your Flask app runs
EXPOSE 5000

# Define the command to run the Flask app
ENTRYPOINT [ "python3" ]
CMD ["app.py"]