# Bedrock Chunking

Welcome to the **Bedrock Chunking** repository! This project provides a custom chunking function designed to support efficient document processing and the creation of a knowledge base for Amazon Bedrock. The implementation uses AWS Lambda and Amazon EFS for managing large language model (LLM) workflows.

## Features

- **Custom Chunking Function**: A scalable chunking method to process documents and prepare them for LLM-based knowledge base indexing.
- **AWS Integration**: Uses AWS Lambda to execute the chunking function, leveraging Amazon EFS to store and access the necessary model.
- **Document Types Supported**: The solution is capable of processing PDFs and other document formats while retaining the images and metadata for more context-aware embeddings.
- **Extracts Tables and Images**: Capable of extracting tables and images from documents to enhance the quality of knowledge representation.
- **Bedrock Knowledge Base Creation**: Prepares the chunked data for Amazon Bedrock, ensuring efficient knowledge representation for retrieval-based tasks.

## Setup

### Prerequisites

- AWS account with permissions to create and manage Lambda functions, EFS, and IAM roles.
- Docker for creating a container image used for the Lambda function.
- Python 3.12+.

### Getting Started

1. **Clone the repository**:

   ```bash
   git clone https://github.com/pranavprasad08/bedrock-chunking.git
   cd bedrock-chunking
   ```

2. **Docker Setup**:
   Build and push the Docker image for your Lambda function. Make sure Docker is installed and running:

   ```bash
   docker build -t bedrock-chunking .
   docker tag bedrock-chunking:latest <your_aws_account_id>.dkr.ecr.<region>.amazonaws.com/bedrock-chunking:latest
   docker push <your_aws_account_id>.dkr.ecr.<region>.amazonaws.com/bedrock-chunking:latest
   ```

3. **Deploy Lambda Function**:
   Update your Lambda function to use the Docker image you've just pushed. Ensure that it has access to an EFS mount for model storage.

4. **Environment Configuration**:
   Update the environment variables as needed, including paths to the EFS mount and any necessary API keys.

## Usage

Once deployed, you can trigger the chunking function via the Lambda console, API Gateway, or any AWS event trigger mechanism. The function will take an input document, process it into structured chunks, and prepare it for indexing in Amazon Bedrock.

## Folder Structure

- **/src**: Contains the source code for the chunking function, including document parsing, metadata extraction, and chunk generation.
- **/docker**: Docker-related files, including the Dockerfile used to create the Lambda container image.
- **/docs**: Documentation and any example inputs/outputs for using the chunking function.
- **/local\_models**: Directory for storing models locally, which can be used during development and testing.

##

