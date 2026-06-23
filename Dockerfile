FROM python:3.14.3-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirments file first (Docker layer caching)
# dependencies only re-install when requirement.txt changes
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY pipeline.py .
COPY data_profiling.py .
COPY data/ data/

# Create the output directory for the generated report
RUN mkdir -p output

# By default, run both the profiling and pipeline scripts when the container starts
# The reports will be written to /app/output inside the container.
CMD ["sh", "-c", "python data_profiling.py && python pipeline.py"]