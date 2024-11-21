from transformers import pipeline 
from PIL import Image
from io import BytesIO
import re
import os

class ImageProcessor:
    def __init__(self):

         # Load a vision model like CLIP
        self.pipe = pipeline("image-to-text", model="./local_models/vit-gpt2-image-captioning") 
    
    def process_images(self, markdown_text, s3_client, bucket_name):
        """
        Creates image summaries and embeddes them into the markdown  and store images in s3 and then update the path to the s3 path
    
        """

        # Pattern to find local image paths in Markdown
        image_pattern = re.compile(r'!\[\]\((.*?)\)')

        # Function to process each match and add metadata
        def add_metadata(match):
            image_path = match.group(1)

            img_name = os.path.basename(image_path)
            key = 'extracted_data/' + img_name

            s3_uri = f"s3://{bucket_name}/{key}"
            
            # Generate the summary using the image summarizer function
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_file.seek(0)
                upload_file(s3_client, bucket_name, key, img_file)
                print(f"Uploaded {image_path} to s3://{bucket_name}/{key}")
                
            image_summary = self.image_summary(img_data)

            # Construct the metadata string
            metadata = f'<!-- image: {s3_uri} summary: "{image_summary}" -->'

            # Return updated Markdown image syntax with metadata
            return f'{metadata}'
    
        # Substitute each image in the markdown with its metadata-enhanced version
        updated_markdown = image_pattern.sub(add_metadata, markdown_text)

        return updated_markdown
    
    def image_summary(self, img_data):
        
        #load images
        image = Image.open(BytesIO(img_data))

        #input image to pipeline
        result = self.pipe(image)
        summary = result[0]['generated_text']  # Extract the generated text
    
        return summary

def upload_file(s3_client, bucket, key, filepath):
    """
    Uploads a single file to S3.
    not currently used 
    """
    
    s3_client.upload_fileobj(filepath, bucket, key, ExtraArgs={'ContentType': 'image/jpeg'})

     
