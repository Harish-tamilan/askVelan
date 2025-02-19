from flask import Flask, request, jsonify
import openai
import os
import logging
from flask_caching import Cache

app = Flask(__name__)

# Configuring cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set your OpenAI API key
openai.api_key = ''

def read_txts_from_folder(folder_path):
    text_content = ""
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content += file.read() + "\n"
    return text_content

def chunk_text(text, max_length=512, overlap=50):
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length <= max_length:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            chunks.append('. '.join(current_chunk))
            current_chunk = current_chunk[-overlap:]  # Keep the last few sentences for overlap
            current_length = sum(len(s.split()) for s in current_chunk)
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append('. '.join(current_chunk))
    
    return chunks

@app.route('/query', methods=['POST'])
def query_documents():
    try:
        data = request.json
        question = data.get('question')
        product_id = data.get('product_id')
        folder_path = os.path.join('assets', product_id)
        
        if not os.path.exists(folder_path):
            return jsonify({"error": "Product not found"}), 404
        
        # Use cache to avoid re-processing text files
        context = cache.get(product_id)
        if not context:
            context = read_txts_from_folder(folder_path)
            cache.set(product_id, context, timeout=5*60)  # Cache for 5 minutes

        chunks = chunk_text(context)
        answers = []
        for chunk in chunks:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Context: {chunk}"},
                    {"role": "user", "content": f"Question: {question}"}
                ]
            )
            answers.append(response.choices[0].message['content'].strip())
        
        # Combine answers or choose the best one
        best_answer = max(answers, key=lambda x: len(x))  # Adjust the key as needed
        
        return jsonify({"answer": best_answer})
    except Exception as e:
        logging.error(f"Error during query: {e}")
        return jsonify({"error": "An error occurred during processing"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
