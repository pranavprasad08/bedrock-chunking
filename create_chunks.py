from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:    
    def __init__(self):
        """
        Initialize chunker
        """
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]     

        self.markdown_splitter = MarkdownHeaderTextSplitter(self.headers_to_split_on, strip_headers = False)
        
        # Char-level splits
        chunk_size = 1024
        chunk_overlap = 100
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk(self, filename, md_text):
        """
        Chunk the document and store the final chunks in self.splits
        :param filename: Path to the source file 
        :param md_text: MD text object

        """
        # MD splits
        md_header_splits = self.markdown_splitter.split_text(md_text) 

        # Split
        splits = self.text_splitter.split_documents(md_header_splits)

        for split in splits:
            split.metadata['source'] = filename

        return splits


# Example Usage 
# chunker = Chunker()
# splits = chunker.chunk('sample_file.md')