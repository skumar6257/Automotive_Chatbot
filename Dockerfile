# Step 1: Start with a lightweight official Python image
FROM python:3.13-slim

# Step 2: Set the working directory inside the container to /app
WORKDIR /app

# Step 3: Copy only the requirements file first. 
# (Docker caches this step, so if you don't change your dependencies, future builds are lightning fast)
COPY requirements.txt .

# Step 4: Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy all your code from your Windows folder into the container's /app folder
COPY . .

# Step 6: Tell Docker that this container listens on port 5000
EXPOSE 5000

# Step 7: The command to run when the container starts
CMD ["python", "app.py"]
