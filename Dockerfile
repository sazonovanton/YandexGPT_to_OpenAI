####################################################################
#         Dockerfile to run OpenAI to YandexGPT Translator         #
#                    Based on an Python Image                      #
####################################################################

# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Run the command to start the app
CMD ["python3", "app.py"]