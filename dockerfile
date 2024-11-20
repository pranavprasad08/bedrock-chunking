# Use the AWS Lambda Python 3.12 base image (change as needed)
FROM public.ecr.aws/lambda/python:3.12

# Copy the entire 'models' folder from the host to the container
COPY local_models ./local_models

# Install dependencies (e.g., pymupdf4llm)
COPY requirements.txt ./
RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy the function code into the container
COPY lambda_function.py ./
COPY process_images.py ./
COPY create_chunks.py ./
COPY process_pdf.py ./

# Command to run your Lambda function
CMD ["lambda_function.lambda_handler"]
 