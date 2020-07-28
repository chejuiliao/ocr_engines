
# OCR engine comparison - Tesseract vs. EasyOCR

This project is exploring different ocr engines and comparing them

This document is for people who want to observe the performance for ocr engines

The codes are running under python3.6 environment

### Step 1: install requirements

open a terminal and run `pip3 install -r requirements.txt`

### Step 2: run python script

In the terminal, run `python3 test_ocr.py <test_size> <test_type>`

e.g. `python3 test_ocr.py 100 number`

`test_size`: how many samples to test, default is `1000`

`test_type`: test on text or number, default is `text`
