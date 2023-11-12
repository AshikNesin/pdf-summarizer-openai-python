from pypdf import PdfReader
import os
from nltk.tokenize import sent_tokenize
from io import StringIO
import json
from openai import OpenAI
import argparse

def read_pdf(filename):
    context = ""
    reader = PdfReader(filename)
    number_of_pages = len(reader.pages)
    # Loop through each page in the PDF file
    for page_num in range(number_of_pages):
        # Get the current page
        page = reader.pages[page_num]
        # Get the text from the current page
        page_text = page.extract_text()
        # Append the text to context
        context += page_text
    return context

def split_text(text, chunk_size=5000):
    """
    Splits a given text into chunks of a specified size.

    Args:
        text (str): The text to be split into chunks.
        chunk_size (int, optional): The maximum size of each chunk. Defaults to 5000.

    Returns:
        list: A list of text chunks.

    """
    chunks = []
    current_chunk = StringIO()
    current_size = 0
    sentences = sent_tokenize(text)

    for sentence in sentences:
        sentence_size = len(sentence)

        if sentence_size > chunk_size:
            while sentence_size > chunk_size:
                chunk = sentence[:chunk_size]
                chunks.append(chunk)
                sentence = sentence[chunk_size:]
                sentence_size -= chunk_size
                current_chunk = StringIO()
                current_size = 0

        if current_size + sentence_size < chunk_size:
            current_chunk.write(sentence)
            current_size += sentence_size
        else:
            chunks.append(current_chunk.getvalue())
            current_chunk = StringIO()
            current_chunk.write(sentence)
            current_size = sentence_size

    if current_chunk:
        chunks.append(current_chunk.getvalue())

    return chunks

def gpt3_completion(prompt, model='gpt-3.5-turbo', max_tokens=1000):
    """
    Generates a GPT-3 completion based on a given prompt.

    Args:
        prompt (str): The prompt to generate the completion from.
        model (str, optional): The GPT-3 model to use for the completion. Defaults to 'gpt-3.5-turbo'.
        max_tokens (int, optional): The maximum number of tokens in the generated completion. Defaults to 1000.

    Returns:
        str: The generated GPT-3 completion.

    Raises:
        Exception: If there is an error while generating the completion.
    """
    # Defaults to os.environ.get("OPENAI_API_KEY")
    # Otherwise use: api_key="Your_API_Key" during OpenAI installation
    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as error:
        return f"OpenAI API error: {error}"

def summarize(document, prompt_for_summary):
    """
    Generates a summary of a given document using GPT-3 language model.

    Args:
        document (str): The document to be summarized.

    Returns:
        str: The generated summary of the document.
    """
    chunks = split_text(document)
    summaries = []

    for chunk in chunks:
        prompt = prompt_for_summary + "\n"
        summary = gpt3_completion(prompt + chunk)

        if not summary.startswith("GPT-3 error:"):
            summaries.append(summary)

    return "".join(summaries)

#read the pdf file

# Create an argument parser
parser = argparse.ArgumentParser()

# Add an argument for the input path
parser.add_argument('--input', help='Path to the input PDF file')
parser.add_argument('--prompt-for-summary', help='Prompt for Summary', default="Please summarize the following document:")


# Parse the command-line arguments
args = parser.parse_args()

# Get the input path from the argument
input_path = args.input
# It handle both Windows and Unix-style file paths. It automatically handles the correct path format based on the operating system.

prompt_for_summary = args.prompt_for_summary

document = read_pdf(input_path)

summary = summarize(document, prompt_for_summary)

print(summary)
