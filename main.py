import os
import requests
from vtracer import convert_image_to_svg_py
from flask import Flask, request, render_template_string, send_file
import tempfile

# HTML template for the upload page
UPLOAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Image to Vector Converter</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        form { text-align: center; }
        input[type="file"] { margin: 10px 0; }
        select { margin: 10px 0; padding: 5px; }
        input[type="submit"] { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background: #45a049; }
        .error { color: red; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Image to Vector Converter</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="image" accept="image/*" required>
            <br>
            <label>Color Mode:</label>
            <select name="colormode">
                <option value="color">Color</option>
                <option value="binary">Binary (B&W)</option>
            </select>
            <br>
            <input type="submit" value="Convert to SVG">
        </form>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

def download_image(url, save_path):
    """Download an image from a URL and save it to the specified path."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            return False, f"URL does not point to an image (content-type: {content_type})."
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True, f"Image downloaded to: {save_path}"
    except Exception as e:
        return False, f"Error downloading image: {e}"

def image_to_vector_vtracer(input_path, output_path, **kwargs):
    """
    Converts a raster image to SVG using vtracer.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"The file {input_path} was not found.")
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Converting {input_path} to SVG...")

    try:
        convert_image_to_svg_py(
            input_path,
            output_path,
            colormode=kwargs.get('colormode', 'color'),
            hierarchical=kwargs.get('hierarchical', 'stacked'),
            mode=kwargs.get('mode', 'spline'),
            filter_speckle=kwargs.get('filter_speckle', 4),
            color_precision=kwargs.get('color_precision', 6),
            layer_difference=kwargs.get('layer_difference', 16),
            corner_threshold=kwargs.get('corner_threshold', 60),
            length_threshold=kwargs.get('length_threshold', 10),
            max_iterations=kwargs.get('max_iterations', 10),
            splice_threshold=kwargs.get('splice_threshold', 45),
            path_precision=kwargs.get('path_precision', 3)
        )
        print(f"Success! Vector saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload():
    error = None
    if request.method == 'POST':
        file = request.files.get('image')
        colormode = request.form.get('colormode', 'color')
        if file and file.filename:
            # Check if it's an image
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                error = "Please upload a valid image file (PNG, JPG, GIF, BMP)."
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1] or '.jpg') as temp_input:
                    file.save(temp_input.name)
                    temp_output = temp_input.name + '.svg'
                    success = image_to_vector_vtracer(temp_input.name, temp_output, colormode=colormode)
                    if success:
                        return send_file(temp_output, as_attachment=True, download_name='converted.svg')
                    else:
                        error = "Conversion failed. Please try a different image."
        else:
            error = "No file selected."
    return render_template_string(UPLOAD_HTML, error=error)

if __name__ == "__main__":
    print("Starting Image to Vector Converter web app...")
    print("Open http://localhost:5000 in your browser to upload and convert images.")
    app.run(host='0.0.0.0', port=5000, debug=False)
