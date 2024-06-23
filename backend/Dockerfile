# Use an official Node.js runtime as a parent image
FROM node:14 as node-backend

# Set the working directory
WORKDIR /usr/src/app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 3000

# Run the Node.js application
CMD ["node", "app.js"]

# Use an official Python runtime as a parent image
FROM python:3.8 as python-backend

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 5001

# Run the Python application
CMD ["python", "./services/llmService.py"]
