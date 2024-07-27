document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('encodeForm')?.addEventListener('submit', function(e) {
        e.preventDefault();

        var formData = new FormData(this);

        fetch('/encode', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) return response.blob();
            return response.text().then(text => { throw new Error(text); });
        })
        .then(blob => {
            var url = window.URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'encoded_image.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a); // Clean up
            window.URL.revokeObjectURL(url);
            document.getElementById('result').textContent = 'Encoding successful! Downloading image...';
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('result').textContent = 'Error: ' + error.message;
        });
    });

    document.getElementById('decodeForm')?.addEventListener('submit', function(e) {
        e.preventDefault();

        var formData = new FormData(this);

        fetch('/decode', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) return response.blob();
            return response.text().then(text => { throw new Error(text); });
        })
        .then(blob => {
            var url = window.URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'decoded_file.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a); // Clean up
            window.URL.revokeObjectURL(url);
            document.getElementById('decodeResult').textContent = 'Decoding successful! Downloading file...';
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('decodeResult').textContent = 'Error: ' + error.message;
        });
    });
});
