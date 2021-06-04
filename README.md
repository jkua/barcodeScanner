# UPC Scanner
This application uses a webcam feed to scan barcodes (UPC, EAN, etc.) and optionally write them to a CSV file

## Dependencies
* python 3.7+
* OpenCV 3+ with Python bindings
* pyzbar
* simpleaudio

### Mac OSX
1. `brew install opencv`
2. `brew install zbar`
3. `pip3 install pyzbar`
4. `pip3 install simpleaudio`

### Linux (Debian/Ubuntu)
1. `sudo apt-get install libzbar0 python3-opencv`
2. `pip3 install pyzbar`
3. `pip3 install simpleaudio`

## Quickstart
1. `./scanner.py`

Run `./scanner.py -h` to see all available options
