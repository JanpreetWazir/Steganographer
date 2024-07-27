from flask import Flask, request, send_file, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
from secret_pixel import hide_file_in_png, extract_file_from_png
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'bmp', 'tga', 'tiff', 'txt', 'pem'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    file_extension = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and file_extension in ALLOWED_EXTENSIONS

def generate_keys(passphrase):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    encryption_algorithm = serialization.BestAvailableEncryption(passphrase.encode('utf-8'))

    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm
    )

    private_key_path = os.path.join(app.config['UPLOAD_FOLDER'], "myprivatekey.pem")
    with open(private_key_path, "wb") as f:
        f.write(pem_private)

    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    public_key_path = os.path.join(app.config['UPLOAD_FOLDER'], "mypublickey.pem")
    with open(public_key_path, "wb") as f:
        f.write(pem_public)

    return private_key_path, public_key_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode_page')
def encode_page():
    return render_template('encode_page.html')

@app.route('/decode_page')
def decode_page():
    return render_template('decode_page.html')

@app.route('/encode', methods=['POST'])
def encode():
    passphrase = request.form.get('passphrase')
    if not passphrase:
        return 'Missing passphrase', 400

    private_key_path, public_key_path = generate_keys(passphrase)

    if 'image' not in request.files or 'secretFile' not in request.files:
        return 'Missing files', 400

    image = request.files['image']
    secret_file = request.files['secretFile']

    if image.filename == '' or secret_file.filename == '':
        return 'No selected files', 400

    if image and allowed_file(image.filename) and secret_file and allowed_file(secret_file.filename):
        image_filename = secure_filename(image.filename)
        secret_filename = secure_filename(secret_file.filename)

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + image_filename)
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_with_keys.zip')

        image.save(image_path)
        secret_file.save(secret_path)

        try:
            hide_file_in_png(image_path, secret_path, output_path, public_key_path)

            # Create a ZIP file containing the encoded image and private key
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(output_path, 'encoded_image.png')
                zipf.write(private_key_path, 'private_key.pem')

            return send_file(zip_path, as_attachment=True, download_name='encoded_image_with_keys.zip')
        except Exception as e:
            return str(e), 500
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(secret_path):
                os.remove(secret_path)
            if os.path.exists(public_key_path):
                os.remove(public_key_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(zip_path):
                os.remove(zip_path)

    return 'Invalid file type', 400

@app.route('/decode', methods=['POST'])
def decode():
    if 'encodedImage' not in request.files or 'privateKey' not in request.files:
        return 'Missing files', 400

    encoded_image = request.files['encodedImage']
    private_key = request.files['privateKey']
    passphrase = request.form.get('passphrase')

    if not passphrase:
        return 'Missing passphrase', 400

    if encoded_image.filename == '' or private_key.filename == '':
        return 'No selected files', 400

    if encoded_image and allowed_file(encoded_image.filename) and private_key and allowed_file(private_key.filename):
        encoded_image_filename = secure_filename(encoded_image.filename)
        private_key_filename = secure_filename(private_key.filename)

        encoded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], encoded_image_filename)
        private_key_path = os.path.join(app.config['UPLOAD_FOLDER'], private_key_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'decoded_output.txt')

        encoded_image.save(encoded_image_path)
        private_key.save(private_key_path)

        try:
            extract_file_from_png(encoded_image_path, output_path, private_key_path, passphrase)

            return send_file(output_path, as_attachment=True, download_name='decoded_file.txt')
        except Exception as e:
            return str(e), 500
        finally:
            if os.path.exists(encoded_image_path):
                os.remove(encoded_image_path)
            if os.path.exists(private_key_path):
                os.remove(private_key_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    return 'Invalid file type', 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
