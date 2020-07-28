def create_img(file: str, text):
    """
    create image with text on white background

    :param file: the path to save the image
    :type file: str
    :param text: the text to write on the image
    :type text: str or float
    :return: None
    :rtype: None
    """
    img = Image.new('RGB', (200, 50), color = (255, 255, 255))  # initialize an empty image
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('arial.ttf', 15)  # set up font
    d.text((10,10), str(text), font=fnt, fill=(0,0,0))  # write text on image
    img.save(file)
    img.close()

def parse_xml(xml):
    """
    parse xml text to be accessed through xpath

    :param xml: xml text
    :type xml: str
    :return: parsel.selector.Selector
    :rtype: object
    """
    # setup xml parser
    parsel.Selector.__str__ = parsel.Selector.extract
    parsel.Selector.__repr__ = parsel.Selector.__str__
    parsel.SelectorList.__repr__ = lambda x: '[{}]'.format(
        '\n '.join("({}) {!r}".format(i, repr(s))
                   for i, s in enumerate(x, start=1))
    ).replace(r'\n', '\n')

    doc = parsel.Selector(text=xml)
    return doc

def tesseract_read(file: str):
    """
    extract text from the image using Tesseract

    :param file: path to the image
    :type file: str
    :return: text
    :rtype: str
    """
    hocr = pytesseract.image_to_pdf_or_hocr(file, extension='hocr')  # convert file to hocr format
    xml = hocr.decode('utf-8')
    doc = parse_xml(xml)  # make the xml accessible by xpath
    tsa_output = []

    # get text
    for tag in doc.xpath('/html/body/div/div/p/span/span'):
        tsa_output.append(str(tag.xpath('text()')[0]))

    tsa_output = " ".join(tsa_output).lower()  # lowercase the output to be better compared with easyocr
    tsa_output = tsa_output.replace('-', ' ')  # replace '-' to be better compared with easyocr
    
    return tsa_output

def easyocr_read(file: str):
    """
    extract text from the image using EasyOCR

    :param file: path to the image
    :type file: str
    :return: text
    :rtype: str
    """
    reader = easyocr.Reader(['th','en'], gpu = True)
    results = reader.readtext(file)
    results = sorted(results, key=lambda x: x[0][0])  # sort text from left to right
    text_results = [x[-2] for x in results][0]  # get text
    easy_output = text_results.strip()  # clean unnecessary space
    
    return easy_output

def compare_diff(df, wrong_column: str, answer_column: str):
    """
    compare the differences between two columns from a dataframe

    :param df: dataframe with wrong and answer column
    :type df: dataframe
    :param wrong_column: name of wrong column
    :type wrong_column: str
    :param answer_column: name of answer column
    :type answer_column: str
    :return:
    :rtype:
    """

    df = df.copy()
    df['add'] = ''  # characters that need to be added to match answer
    df['delete'] = ''  # characters that need to be deleted to match answer
    for idx, row in df.iterrows():  # iterate through each row
        a = row[wrong_column]  # ocr engine's output
        b = row[answer_column]  # answer
        add_list = []
        delete_list = []
        for i,s in enumerate(difflib.ndiff(a, b)):  # iterate through the differences
            if s[0]==' ': continue
            elif s[0]=='-':  # characters that need to be deleted to match answer
                delete_list.append(s[-1])
            elif s[0]=='+':  # characters that need to be added to match answer
                add_list.append(s[-1])
        if len(delete_list) > 0:
            df.loc[idx, 'delete'] = "|".join(delete_list)
        if len(add_list) > 0:
            df.loc[idx, 'add'] = "|".join(add_list)

    return df

if __name__ == '__main__':
    from random_words import RandomWords
    from PIL import Image, ImageDraw, ImageFont
    import random
    import time
    import pytesseract
    import easyocr
    import parsel
    import numpy as np
    import pandas as pd
    import difflib
    import sys

    try:  # check if test size is given
        test_size = int(sys.argv[1])
    except:
        test_size = 100

    try:  # check if test type is given
        test_type = sys.argv[2]  # text or number
    except:
        test_type = 'text'

    file = 'test_img.jpg'
    answer_list = []
    tsa_list = []
    easy_list = []
    tsa_time_used = 0
    easy_time_used = 0
    rw = RandomWords()  # used to generate random words
    for i in range(test_size):
        print(i)
        cont = 1

        # create data
        if test_type == 'number':
            text = str(round(random.uniform(10000, 99999),2))
        elif test_type == 'text':
            text = " ".join(rw.random_words(count=2))  # generate two words
            text = text.replace('-', ' ')  # replace '-' since easyocr doesn't interpret '-'
            if len(text) > 22:  # in case the text is beyond the image size
                text = text[:22]

        create_img(file, text)  # create the image with text
        
        # get result from tesseract
        tsa_start_time = time.time()
        tsa_result = tesseract_read(file)
        tsa_end_time = time.time()
        tsa_time_used = tsa_time_used + (tsa_end_time-tsa_start_time)/60
        
        # get result from easyocr
        easy_start_time = time.time()
        easy_result = easyocr_read(file)
        easy_end_time = time.time()
        easy_time_used = easy_time_used + (easy_end_time-easy_start_time)/60
        
        # append result
        answer_list.append(text.lower())
        tsa_list.append(tsa_result)
        easy_list.append(easy_result)

    # convert to array
    answer_array = np.array(answer_list)
    tsa_array = np.array(tsa_list)
    easy_array = np.array(easy_list)

    # calculate error rates
    tsa_error_rate = np.mean(answer_array!=tsa_array) * 100
    easy_error_rate = np.mean(answer_array!=easy_array) * 100

    # print out error rates
    print(f"Tesseract error rate on {test_size} samples: {tsa_error_rate}%, used {tsa_time_used} minutes")
    print(f"EasyOCR error rate on {test_size} samples: {easy_error_rate}%, used {easy_time_used} minutes")

    # store wrong cases and answer in dataframe
    df_tsa_wrong = pd.DataFrame({'tsa_wrong': tsa_array[tsa_array!=answer_array], 'answer': answer_array[tsa_array!=answer_array]})
    df_easy_wrong = pd.DataFrame({'easy_wrong': easy_array[easy_array!=answer_array], 'answer': answer_array[easy_array!=answer_array]})

    df_tsa_wrong_diff = compare_diff(df_tsa_wrong, 'tsa_wrong', 'answer')
    df_easy_wrong_diff = compare_diff(df_easy_wrong, 'easy_wrong', 'answer')

    # output dataframe as csv
    df_tsa_wrong.to_csv('tsa_wrong_diff.csv')
    df_easy_wrong.to_csv('easy_wrong_diff.csv')

