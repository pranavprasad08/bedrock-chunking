import pymupdf4llm
import pathlib
from io import BytesIO
import re
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class PDFProcessor:
    def __init__(self, image_processor, chunker, output_dir=f"/tmp/", image_dir=f"/tmp/"):
        """
        Initializes the PDFProcessor with the data table file and the directory for images.
        
        :param file: Path to the PDF file 
        :param output_dir: Directory where extracted images will be stored
        :param image_dir: Directory where extracted images will be stored
        """
        self.output_dir = output_dir
        self.image_dir = image_dir

        # Load a vision model like CLIP
        self.image_processor = image_processor
        self.chunker = chunker

        # initialize logger
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)

        os.environ["TRANSFORMERS_CACHE"] = "/tmp"

    def convert_to_markdown(self, filename, s3_client, bucket_name):
        """
        Converts PDF to Markdown with images and saves it.
        
        :param doc: PyMuPDF document object with metadata
        :param filename: Original filename of the PDF, used to generate the Markdown filename
        """
        # Convert to Markdown and save images to the specified image directory
        pages = pymupdf4llm.to_markdown(filename, page_chunks=True, write_images=True, image_path=self.image_dir, image_format='jpg')
        self.logger.info("{filename} parsed")

        md_text = ""

        for page in pages:
            text = page['text']
            page_no = page['metadata']['page']
            text, images = self.image_processor.process_images(text, s3_client, bucket_name)
            self.logger.info(f"{filename, page_no} images prorcessed")
            md_text += text
        
        # Save Markdown content to a file
        s3_md_key = f"parsed_files/{pathlib.Path(filename).stem}.md"
        write_md_to_s3(s3_client, bucket_name, s3_md_key, md_text)

        self.logger.info(f"Markdown file saved as: {s3_md_key}")

        # Save images to s3
        with ThreadPoolExecutor(max_workers=8) as executor:
            for key, img_file in images.items():
                write_img_to_s3(s3_client, bucket_name, key, img_file)

        return md_text


    def process_pdf(self, filename, s3_client, bucket_name):
        """
        Process the PDF by converting to Markdown and creating Chunks.
        
        """
        
        # Convert to Markdown and save
        md_text = self.convert_to_markdown(filename, s3_client, bucket_name)

        self.logger.info(f"Processed {filename} with images and metadata.")

        splits = self.chunker.chunk(filename, md_text)

        chunked_content = {
        'fileContents': []
        }

        for chunk in splits:
            chunked_content['fileContents'].append({
                    'contentType': 'str',
                    'contentMetadata': chunk.metadata,
                    'contentBody': chunk.page_content
                })
            
        self.logger.info(f"{filename}content chunked")

        return chunked_content
    


def write_img_to_s3(s3_client, bucket, key, content): 
    with open(content, 'rb') as file:
        s3_client.upload_fileobj(file, bucket, key, ExtraArgs={'ContentType': 'image/jpeg'})
   
def write_md_to_s3(s3_client, bucket, key, content):
    s3_client.put_object(Bucket=bucket, Key=key, Body=content, ContentType='text/markdown')    


# Example usage
# processor = PDFProcessor()
# chunks = processor.process_pdf("your_file.pdf")
