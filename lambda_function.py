import json
import os
from process_pdf import PDFProcessor
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
from create_chunks import Chunker
from process_images import ImageProcessor

def lambda_handler(event, context):
    logger.debug('input={}'.format(json.dumps(event)))
    s3 = boto3.client('s3')

    # Extract relevant information from the input event
    input_files = event.get('inputFiles')
    input_bucket =  event.get('bucketName')

    
    if not all([input_files, input_bucket]):
        raise ValueError("Missing required input parameters")
    
    output_files = []

    # Load a image processor and chunker
    image_processor = ImageProcessor()
    chunker = Chunker()
    processor = PDFProcessor(image_processor=image_processor, chunker=chunker)

    for input_file in input_files:
        content_batches = input_file.get('contentBatches', [])
        file_metadata = input_file.get('fileMetadata', {})
        original_file_location = input_file.get('originalFileLocation', {})
        org_file_uri = original_file_location['s3_location']['uri']

        processed_batches = []
        
        for batch in content_batches:
            input_key = batch.get('key')

            if not input_key:
                raise ValueError("Missing uri in content batch")
            
            org_bucket_name = org_file_uri.split('/')[2]
            org_file_key = '/'.join(org_file_uri.split('/')[3:])
            
            # Read file from S3
            file_path = read_s3_file(s3, org_bucket_name, org_file_key)
            
            # Process content (chunking)
            chunked_content = processor.process_pdf(file_path, s3, input_bucket)
            
            # Write processed content back to S3
            write_to_s3(s3, input_bucket, input_key, chunked_content)
            
            # Add processed batch information
            processed_batches.append({
                'key': input_key
            })
        
        # Prepare output file information
        output_file = {
            'originalFileLocation': {
                "type": "S3",
                "s3_location":original_file_location['s3_location']
                },
            'fileMetadata': file_metadata,
            'contentBatches': processed_batches
        }
        output_files.append(output_file)
    
    result = {'outputFiles': output_files}

    return result
    

def read_s3_file(s3_client, bucket, key):
    file_path = '/tmp/' + key
    s3_client.download_file(bucket, key, file_path)
    return file_path

def write_to_s3(s3_client, bucket, key, content):
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(content))    

