from flask import Flask, request, jsonify, send_from_directory, send_file
import os
from werkzeug.utils import secure_filename
from langchain_community.document_loaders.image import UnstructuredImageLoader
import json
from langchain_community.document_loaders import PyMuPDFLoader
import os
from dotenv import load_dotenv
load_dotenv()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf','webp'}
HTML_FOLDER = 'static'
HTML_FILE = 'index.html'


# Create the uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """ Check if the file extension is allowed """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

prompt_pre= """
follwoing text in extracted from a invoice file. now get the data from it and give the output in below json format. give exmpty if the data is not present in given extracted text

OUTPUT FORMAT: { "vendor_name":"name of vendor if present",
                "vendor_address":"address of vendor if present",
                "vendor_country":"country of vendor",
                "invoice_date":"invoice date if present in DD/MM/YYYY format",
                "invoice_number":"invoice number",
                "due_date":"due date of invoice if present in DD/MM/YYYY format",
                "total":"invoice total amount without currency",
                "currency": "invoice currency if available",
                "payment_type":"payment type if already paid and present in invoice",
                "description":"a short description of the invoice like for what the invoice is for"
                }
EXTRACTED TEXT:"""

prompt_post="""\n
OUTPUT:
"""

from langchain.llms import OpenAI
llm = OpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"),model= 'gpt-3.5-turbo-instruct')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process_image', methods=['POST'])
def process_image():
    # Check if the image file is in the request
    if 'image' not in request.files:
        return jsonify({'status': 'failed', 'message': 'No file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'failed', 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    
    
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in ['png', 'jpg', 'jpeg','webp']:
            loader = UnstructuredImageLoader(filepath)
        elif ext in ['pdf']:
            loader = PyMuPDFLoader(filepath)
        docs = loader.load()
        content = '*****page_end****'.join([x.page_content for x in docs])
        
        data = json.loads(llm.predict(prompt_pre+content+prompt_post))
        # Return a static JSON response
        return jsonify({
            'status': 'success',
            'message': 'Image processed successfully',
            'filename': filename,
            'processing_details': data
        }), 200
    else:
        return jsonify({'status': 'failed', 'message': 'Invalid file type'}), 400
    
@app.route('/')
def serve_html():
    """Serve the static HTML file."""
    return send_file(os.path.join(HTML_FOLDER, HTML_FILE))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
