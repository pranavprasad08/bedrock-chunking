from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image
import re
import os
import torch 
import json 

class ImageProcessor:
    def __init__(self):
        """
        Initialize the ImageProcessor class with global instructions for the model.
        """
        # Load a vision-language model pipeline
        model_id = './local_models/Florence-2-base'
        
        self.device = "cpu"
        self.torch_dtype = torch.float32

        self.model = AutoModelForCausalLM.from_pretrained(model_id, attn_implementation="sdpa", torch_dtype=self.torch_dtype, trust_remote_code=True)

        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
                
        # Pattern to find local image paths in Markdown
        self.image_pattern = re.compile(r'!\[\]\((.*?)\)')

    def process_images(self, markdown_text, s3_client, bucket_name):
        """
        Processes images in Markdown, uploads them to S3, generates summaries using instructions
        and Markdown text for context, and updates the Markdown with metadata.

        Args:
            markdown_text (str): The Markdown content with image references.
            s3_client (boto3.client): The S3 client object for uploading images.
            bucket_name (str): The S3 bucket name where images will be uploaded.

        Returns:
            str: Updated Markdown text with metadata for each image.
        """

        # Function to process each match and add metadata
        def add_metadata(match):
            image_path = match.group(1)
            img_name = os.path.basename(image_path)
            key = f'extracted_data/{img_name}'
            s3_uri = f"s3://{bucket_name}/{key}"

            # Upload the image to S3
            with open(image_path, 'rb') as img_file:
                self.upload_file(s3_client, bucket_name, key, img_file)

            # Generate image summary with instructions and Markdown context
            image_summary = self.image_summary(image_path, markdown_text)

            # Construct the metadata string
            metadata = f'<!-- image: {s3_uri} summary: "{image_summary}" -->'

            # Return updated Markdown with metadata
            return metadata

        # Replace image references in Markdown with updated ones
        updated_markdown = self.image_pattern.sub(add_metadata, markdown_text)

        return updated_markdown

    def image_summary(self, img_path, markdown_context):
        """
        Generates a summary of the image using instructions and Markdown text for context.

        Args:
            img_data (bytes): Image data in bytes.
            markdown_context (str): The surrounding Markdown text.

        Returns:
            str: Generated summary.
        """
        try:
            # Generate a summary using the pipeline
            task_prompt = '<DETAILED_CAPTION>'
            result = self.run_example(task_prompt, img_path)
            summary=result
        except Exception as e:
            print(f"Error generating summary: {e}")
            summary = "Summary generation failed"

        return summary

    def run_example(self, task_prompt, image):
        image = Image.open(image)
        inputs = self.processor(text=task_prompt, images=image, return_tensors="pt").to(self.device, self.torch_dtype)
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            do_sample=False,
            num_beams=3
            )
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        parsed_answer = self.processor.post_process_generation(generated_text, task=task_prompt, image_size=(image.width, image.height))

        summary = json(parsed_answer)

        return summary[task_prompt]
    
    @staticmethod
    def upload_file(s3_client, bucket, key, filepath):
        """
        Uploads a single file to S3.

        Args:
            s3_client (boto3.client): The S3 client object for uploading.
            bucket (str): The S3 bucket name.
            key (str): The object key for the file.
            filepath (file object): The file object to upload.

        Returns:
            None
        """
        try:
            s3_client.upload_fileobj(filepath, bucket, key, ExtraArgs={"ContentType": "image/jpeg"})
            print(f"Successfully uploaded {key} to {bucket}")
        except Exception as e:
            print(f"Failed to upload {key} to {bucket}: {e}")
    