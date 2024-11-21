import pymupdf4llm
import pathlib
from io import BytesIO
import os
import logging
import zipfile

class PDFProcessor:
    def __init__(self, image_processor, chunker, image_dir=f"/tmp/img/"):
        """
        Initializes the PDFProcessor with the data table file and the directory for images.
        
        :param imag_processor: initialized image processor object
        :param imag_processor: intialized chunker object
        :param image_dir: Directory where extracted images will be stored
        """
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
        self.logger.info(f"{filename} parsed")

        md_text = ""

        for page in pages:
            text = page['text']
            text = self.image_processor.process_images(text, s3_client, bucket_name)
            md_text += text
        self.logger.info(f"{filename} images prorcessed")

        # Save Markdown content to a file
        s3_md_key = f"parsed_files/{pathlib.Path(filename).stem}.md"
        write_md_to_s3(s3_client, bucket_name, s3_md_key, md_text)

        self.logger.info(f"Markdown file saved as: {s3_md_key}")

        # # Compress images to zip and save in s3
        # output_zip_path = f'{filename}.zip'
        # compress_to_zip(self.image_dir, output_zip_path)

        # zip_key = f'extractedZips/{pathlib.Path(filename).stem}.zip'

        # write_obj_to_s3(s3_client, bucket_name, zip_key, output_zip_path)

        # self.logger.info(f"Images file saved as: {zip_key}")

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
    


def write_obj_to_s3(s3_client, bucket, key, content): 
    with open(content, 'rb') as file:
        s3_client.upload_fileobj(file, bucket, key)
   
def write_md_to_s3(s3_client, bucket, key, content):
    s3_client.put_object(Bucket=bucket, Key=key, Body=content, ContentType='text/markdown')    

def compress_to_zip(folder_path, output_zip_path):
    """
    Compress files in a folder into a ZIP file using Python's native zipfile module.
    """
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder_path)  # Keeps folder structure relative
                zipf.write(full_path, arcname)

# Example usage
# processor = PDFProcessor()
# chunks = processor.process_pdf("your_file.pdf")
