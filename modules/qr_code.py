import os
import pyqrcode
import secrets
import png  # Required for pyqrcode to save as PNG
from pathlib import Path

def generate_tokens(n_tokens: int, tokens = [], nbytes = 16) -> list:
    """
    Adds new tokens to an existing array by the number of n_tokens or create a new array with n_tokens. 
    
    :param n_tokens: Number of tokens to add or generate
    :param tokens: List of tokens 
    :param nbytes: Number of bytes for token
    """
    for _ in range(n_tokens):
        while True:
            random_key = secrets.token_urlsafe(nbytes)
            if random_key not in tokens:
                tokens.append(random_key)
                break
    return tokens
        
    


def generate_dynamic_qr(base_url: str, tokens: list, out_path: Path) -> None:
    """
    Generates QR codes for a base URL by appending tokens as query parameters.

    For each token in the list, a URL is constructed (e.g., base_url?token=key),
    and a corresponding QR code is generated and saved as a PNG file in the
    specified output directory.

    :param base_url: The base URL of the website.
    :type base_url: str
    :param tokens: A list of tokens to be used as query parameters.
    :type tokens: list
    :param out_path: The directory path where the QR code images will be saved.
    :type out_path: Path
    """
    for random_key in tokens:
        final_url = f"{base_url}?token={random_key}"

        print(f"Generated URL: {final_url}")
        print(f"Key to parse later: {random_key}")

        # Generate the QR Code
        qr = pyqrcode.create(final_url)

        # Save the file
        # scale=8 makes the pixels larger so it is easier to scan
        filename = f"qr_{random_key}.png"
        out_path = Path(out_path)

        if os.path.exists(out_path) != True:    #If path does not exists, make it
            os.mkdir(out_path)
        file_path = os.path.join(out_path, filename)
        
        qr.png(file_path, scale=8)
        print(f"Success! QR code saved as {file_path}")

