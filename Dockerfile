# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip3 install --upgrade pip

RUN python3 -m pip install --upgrade setuptools

RUN pip3 install --upgrade cython
RUN pip install psycopg2-binary
# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 3000

# Run app.py when the container launches
CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
