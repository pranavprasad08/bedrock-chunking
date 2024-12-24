from transformers import pipeline 
from PIL import Image
from io import BytesIO
import re
import os

class ImageProcessor:
    def __init__(self):
        """
        Initialize the ImageProcessor class with global instructions for the model.
        
        Args:
            instructions (str): Global instructions to guide the model's inference for all images.
        """
        # Load a vision-language model
        self.pipe = pipeline("image-text-to-text", model="./local_models/Qwen2-VL-2B-Instruct")
        self.instructions = "Using the following context from the page, summarize the image for RAG. Make sure to include the relevant context in the summary"
    
    def process_images(self, markdown_text, s3_client, bucket_name):
        """
        Processes images in Markdown, uploads them to S3, generates summaries using instructions
        and Markdown text for context, and updates the Markdown with metadata.
        """
        # Pattern to find local image paths in Markdown
        image_pattern = re.compile(r'!\[\]\((.*?)\)')

        # Function to process each match and add metadata
        def add_metadata(match):
            image_path = match.group(1)
            img_name = os.path.basename(image_path)
            key = f'extracted_data/{img_name}'
            s3_uri = f"s3://{bucket_name}/{key}"
            
            # Upload the image to S3
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_file.seek(0)
                self.upload_file(s3_client, bucket_name, key, img_file)
                print(f"Uploaded {image_path} to {s3_uri}")
            
            # Generate image summary with instructions and Markdown context
            image_summary = self.image_summary(img_data, markdown_text)

            # Construct the metadata string
            metadata = f'<!-- image: {s3_uri} summary: "{image_summary}" -->'

            # Return updated Markdown with metadata
            return metadata
    
        # Replace image references in Markdown with updated ones
        updated_markdown = image_pattern.sub(add_metadata, markdown_text)

        return updated_markdown

    def image_summary(self, img_data, markdown_context):
        """
        Generates a summary of the image using instructions and Markdown text for context.

        Args:
            img_data (bytes): Image data in bytes.
            markdown_context (str): The surrounding Markdown text.

        Returns:
            str: Generated summary.
        """
        # Load the image
        image = Image.open(BytesIO(img_data))

        # Combine instructions and Markdown context
        full_input = f"{self.instructions}\n{markdown_context}"

        # Generate a summary using the model
        try:
            result = self.pipe(image, context=full_input)
            summary = result[0]['generated_text']
        except Exception as e:
            print(f"Error generating summary: {e}")
            summary = "Summary generation failed"
        
        return summary

    def upload_file(self, s3_client, bucket, key, filepath):
        """
        Uploads a single file to S3.
        """
        try:
            s3_client.upload_fileobj(filepath, bucket, key, ExtraArgs={'ContentType': 'image/jpeg'})
            print(f"Successfully uploaded {key} to {bucket}")
        except Exception as e:
            print(f"Failed to upload {key} to {bucket}: {e}")
