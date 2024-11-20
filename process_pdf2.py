import pymupdf4llm
import pathlib
import fitz
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class PDFProcessor:
    def __init__(self, image_processor, chunker, output_dir=f"/tmp/", image_dir=f"/tmp/", max_threads=4):
        """
        Initializes the PDFProcessor with the data table file and the directory for images.
        
        :param output_dir: Directory where extracted images will be stored
        :param image_dir: Directory where extracted images will be stored
        :param max_threads: Maximum number of threads for parallel processing
        """
        self.output_dir = output_dir
        self.image_dir = image_dir
        self.image_processor = image_processor
        self.chunker = chunker
        self.max_threads = max_threads

        # Initialize logger
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)

        os.environ["TRANSFORMERS_CACHE"] = "/tmp"

    def _process_pages(self, filename, pages, s3_client, bucket_name):
        """
        Process specific pages from the PDF into Markdown and handle images.
        
        :param filename: Path to the PDF file
        :param pages: List of page numbers to process
        :param s3_client: Boto3 S3 client object
        :param bucket_name: Name of the S3 bucket
        :return: Processed Markdown text for the given pages
        """
        pages_result = pymupdf4llm.to_markdown(
            filename,
            page_chunks=True,
            write_images=True,
            image_path=self.image_dir,
            image_format='jpg',
            pages=pages
        )
        self.logger.info(f"Processed pages {pages} of {filename}")

        md_text = ""
        for page in pages_result:
            text = page['text']

            # Process images within the page
            text = self.image_processor.process_images(text, s3_client, bucket_name)
            md_text += text
        
        return md_text

    def convert_to_markdown(self, filename, s3_client, bucket_name):
        """
        Converts PDF to Markdown with images and saves it.
        
        :param filename: Original filename of the PDF, used to generate the Markdown filename
        :param s3_client: Boto3 S3 client object
        :param bucket_name: Name of the S3 bucket
        """
        # Get total pages and calculate ranges
        doc = fitz.open(filename)
        num_pages = doc.page_count

        chunk_size = -(-num_pages // self.max_threads)  # Ceiling division for chunk size
        page_ranges = [list(range(i, min(i + chunk_size, num_pages))) for i in range(0, num_pages, chunk_size)]

        futures = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for pages in page_ranges:
                futures.append(
                    executor.submit(self._process_pages, doc, pages, s3_client, bucket_name)
                )

        md_text = ""
        for future in as_completed(futures):
            md_text += future.result()

        # Save Markdown content to a file in S3
        s3_md_key = f"parsed_files/{pathlib.Path(filename).stem}.md"
        write_md_to_s3(s3_client, bucket_name, s3_md_key, md_text)

        self.logger.info(f"Markdown file saved as: {s3_md_key}")

        doc.close()

        return md_text

    def process_pdf(self, filename, s3_client, bucket_name):
        """
        Process the PDF by converting to Markdown and creating Chunks.
        
        :param filename: Path to the PDF file
        :param s3_client: Boto3 S3 client object
        :param bucket_name: Name of the S3 bucket
        """
        # Convert to Markdown and save
        md_text = self.convert_to_markdown(filename, s3_client, bucket_name)

        self.logger.info(f"Processed {filename} with images and metadata.")

        # Chunk the Markdown content
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
        
        self.logger.info(f"{filename} content chunked")

        return chunked_content


def write_img_to_s3(s3_client, bucket, key, content): 
    with open(content, 'rb') as file:
        s3_client.upload_fileobj(file, bucket, key, ExtraArgs={'ContentType': 'image/jpeg'})


def write_md_to_s3(s3_client, bucket, key, content):
    s3_client.put_object(Bucket=bucket, Key=key, Body=content, ContentType='text/markdown')
    

# Example usage
# processor = PDFProcessor(image_processor=some_processor, chunker=some_chunker)
# chunks = processor.process_pdf("your_file.pdf", s3_client=some_s3_client, bucket_name="your_bucket")
