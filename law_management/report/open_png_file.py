# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64


def get_png_file(file):
    with open(file, "rb") as png_file:
        encoded_string = base64.b64encode(png_file.read())
    return encoded_string
