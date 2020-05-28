"""Este módulo contém uma série de funções que auxiliam no processamento dos captchas:

Filtros são aplicados em imagens em escala de cinza.

Imagens sem qualidade de processamento geram um log em nível de warning em arquivo .log
Logs de info são direcionados para o console, caso disponível. Para configurar os logs,
consultar o arquivo logging.conf

 1) _BIN + OTSU: Aplica, na sequência, os fitros Gaussian Blur, Thresholds binário + OTSU.

 2) _count_black_pixels: conta a quantidade de pixels pretos numa dada imagem.

 3) _captcha_filter: wraper de funções que permite aplicar o Treshold Binário + Median Blur
 ou então apenas Threshold Binário + OTSU, a depender do filter mode utilizado.

 4) captcha_interpreter: processa os captchas baseado no número de pixels obtidos
 após a filtragem por Median Blur. A depender da qualidade da imagem processada,
 utiliza a engine Tesseract para decidir sobre qual imagem utilizar.

 5) _trim_digits: função auxiliar para realizar o corte em dígitos que 
 eventualmente tenham ficados "siameses".

 6) grab_digits: Com base em uma imagem já processada, individualiza os dígitos, retornando-os na
 sequência em que aparecem na imagem.
 
 7) resize_to_fit: Padroniza os dígitos processados em arrays de (n x n).
 
 8) Funciona como wrapper para todas as funções acima. """

import os
import logging
import logging.config

import pytesseract as ocr
from cv2 import cv2
import numpy as np

os.chdir(os.path.dirname(__file__))

# Configura o display e salvamento de logs
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("root")


def _BIN_and_OTSU(img: object):

    # Aplicando o filtro gaussian blur para preservar os edges
    gauss_blur = cv2.GaussianBlur(img, (3, 3), 0)

    # Aplicando o threshold Binário + OTSU na imagem com filtro gaussiano
    img_th2 = cv2.threshold(gauss_blur, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    black_pixels = _count_black_pixels(img_th2)

    if black_pixels > 0.80 * img.size:
        img_th2 = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    return img_th2


def _dilate(img: object):

    kernel = np.ones((2, 2), np.uint8)

    erosion = cv2.erode(img, kernel, iterations=1)
    dilate = cv2.dilate(erosion, kernel, iterations=1)

    return dilate


def _count_black_pixels(img: object):

    black_pixels = img.size - cv2.countNonZero(img)

    return black_pixels


def _captcha_filter(img: object, filter_mode=None):
    """Favor documentar a lógica aqui... """

    if filter_mode == "Median Blur":
        # Aplicação de threshold Binário + OTSU na imagem original escala de cinza
        img_th1 = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Contando os pixels que não pretos (val = 0)
        black_pixels = _count_black_pixels(img_th1)

        if black_pixels > 0.80 * img.size:
            img_th1 = cv2.threshold(
                img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )[1]

        # Aplicação de median blured
        img_blur = cv2.medianBlur(img_th1, 3)

        return (img_blur, _count_black_pixels(img_blur))

    elif filter_mode == "Binary + OTSU":
        bin_otsu_img = _BIN_and_OTSU(img)

        return (bin_otsu_img, _count_black_pixels(bin_otsu_img))


def captcha_interpreter(file_name=None, **kwargs):
    """**kwargs = captcha_bytes, fund_name são argumentos opcionais
    Função trabalha em dois modos:
    
    1) Lendo os arquivos a partir de um diretório indicado, neste caso,
    file_name = full_path_to_the_file

    2) Recebendo o stream de bytes com o nome "captcha_bytes" e convertendo-o para figura. """

    if kwargs is not None and file_name is None:

        logger.info(f"Processando o streaming de bites.")
        try:
            _captcha = kwargs.get("captcha_bytes")
            picture = cv2.imdecode(np.asarray(bytearray(_captcha), dtype="uint8"), 0)
            file_name = f'Captcha_{kwargs.get("fund_name")}'
        except Exception as err:
            logger.exception(f"Ocorreu o seguinte erro: {err}.")
            return np.empty(0)

    else:

        logger.info(f"Processando a imagem: {file_name}.")
        try:
            picture = cv2.imread(file_name, 0)

        except Exception as err:
            logger.exception(f"Erro de leitura no arquivo {file_name}: {err}.")
            return np.empty(0)

    # Obtendo as dimensões da figura
    picture_size = picture.size
    median_blur_result, median_blur_pixels = _captcha_filter(
        picture, filter_mode="Median Blur"
    )

    if median_blur_pixels <= (3 / 100) * picture_size:

        logger.info(f"Imagem {file_name}: Baixa qualidade de processamento.")

        TH_bin_result, TH_bin_pixels = _captcha_filter(
            picture, filter_mode="Binary + OTSU"
        )

        if TH_bin_pixels > (4 / 100) * picture_size:

            logger.info(
                f"Imagem {file_name}: Foi possível extrair dígitos a partir de Gauss + Bin + OTSU."
            )

            return _dilate(TH_bin_result)
        else:

            logger.warning(f"Imagem {file_name}: Não foi possível processar.")
            return np.empty(0)

    elif 3 / 100 * picture_size < median_blur_pixels < 5 / 100 * picture_size:

        logger.info(f"Imagem {file_name}: Qualidade média de processamento.")

        TH_bin_result, _ = _captcha_filter(picture, filter_mode="Binary + OTSU")

        images = [median_blur_result, TH_bin_result]
        candidates = [
            ocr.image_to_string(
                image, config="--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789"
            )
            for image in images
        ]

        # Se não houver interpretação em nenhum dos casos, utilizar TH-BIN
        if all(i == "" for i in candidates):
            logger.debug(
                f"Imagem {file_name}: Tesseract não identificou dígitos na imagem processada. Retornado Bin+OTSU."
            )
            return TH_bin_result

        # Se uma das imagens não possuir interpretação, retorne esta imagem
        elif "" in candidates:
            logger.debug(
                f"Imagem {file_name}: Tesseract identificou pelo menos um dígito."
            )
            return [
                image for candidate, image in zip(candidates, images) if candidate != ""
            ][0]

        else:

            # Se as duas tiverem o mesmo número de caracteres, me retorne a com maior densidade de pixels
            if max(candidates, key=len) == min(candidates, key=len):
                logger.debug(
                    f"Imagem {file_name}: utilizado BIN + OTSU por apresentar maior densidade de pixels."
                )
                return TH_bin_result
            # Se as duas possuirem interpretação retorne a que tiver mais caracteres
            else:
                logger.debug(
                    f"Imagem {file_name}: Retornada a opção na qual o Tesseract identificou mais caracteres."
                )
                return [
                    image
                    for candidate, image in zip(candidates, images)
                    if candidate == max(candidates, key=len)
                ][0]

    # Se median blur detectou mais de 5% de pixels, retorne medium blur
    else:
        logger.info(
            f"Imagem {file_name}: Boa qualidade de processamento por Median-Blur."
        )
        return median_blur_result


def _trim_digits(element, average: int, picture: object):

    x, y, w, h = element
    factor = round(w / average)
    delta = w // factor
    trimmed_data = []

    for _ in range(0, factor):

        # Cortando com um pixel de margem para cada lado
        trimmed_data.append((picture[y - 1 : y + h + 1, x - 1 : x + delta + 1], x))
        x = x + delta

    return trimmed_data


def grab_digits(img: object, file_name: str) -> list:
    """A partir de uma imagem processada previamente irá realizar o seguinte:
    
    1) Inverte os pixels com bitwise.
    2) Encontra os contornos que delimitam os dígitos.
    3) Realiza o corte caso vários dígitos sejam interpretados juntos
    4) Retorna os dígitos na ordem em que aparecem na imagem."""

    adjusted_img = cv2.resize(img, (0, 0), fx=2, fy=2)
    processed_img = cv2.bitwise_not(adjusted_img)

    contours, _ = cv2.findContours(
        processed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    interpreted_digits = []
    labels = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w > 10 and h > 10:
            labels.append((x, y, w, h))

    # Ordenando com base nas maiores larguras w e desconsiderando o dígito de maior largura:
    sorted_labels = sorted(labels, key=lambda e: e[2])[:-1]
    size_sorted_labels = len(sorted_labels)

    # Caso tenham sido interpretados somente 3 dígitos, usa a largura mínima no lugar da média
    if size_sorted_labels >= 3:
        average = sum(i for _, _, i, _ in sorted_labels) / size_sorted_labels
    elif size_sorted_labels >= 2:
        average = min(labels, key=lambda e: e[2])[2]
    else:
        logger.debug(
            f"Imagem {file_name}: Não foi possível isolar os dígitos na imagem."
        )
        return []

    for element in labels:
        x, y, w, h = element

        if w / average > 1.5:
            logger.debug(f"Imagem {file_name}: Realizados cortes adicionais na imagem.")
            interpreted_digits = interpreted_digits + _trim_digits(
                element, average, picture=processed_img
            )
        else:
            # Cortando com um pixel de margem para cada lado
            interpreted_digits.append(
                (processed_img[y - 1 : y + h + 1, x - 1 : x + w + 1], x)
            )

    # Retorna os digitos interpretados e na ordem em que ocorrem na imagem
    logger.info(f"Imagem {file_name}: Processada com sucesso.")
    return [digits for digits, x in sorted(interpreted_digits, key=lambda e: e[1])]


def resize_to_fit(img: object, new_size: int) -> object:

    """Resizes the image to new squared dimension (dim: new_size) keeping the 
    proportions and padding with black pixels"""

    # shape retorna (h, w)
    ratio = new_size / (max(img.shape[:2]))

    new_shape = tuple([int(ratio * size) for size in img.shape[:2]])

    # Realizando o resize na proporção calculada. Resize usa (w,h)
    new_img = cv2.resize(img, (new_shape[1], new_shape[0]))

    # Ajustando o pad para cada uma das dimensões (w e h)
    total_padw = new_size - new_img.shape[1]
    pad_right = total_padw // 2
    pad_left = total_padw - pad_right

    total_padh = new_size - new_img.shape[0]
    pad_top = total_padh // 2
    pad_bottom = total_padh - pad_top

    new_img = cv2.copyMakeBorder(
        new_img, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT
    )

    return new_img


def digits_extractor(bites_stream, filename):
    """Definições:
     - bites_steam: captcha em bites.
     - filename: no geral, o nome do fundo.
     
     A função recebe o captcha em bites, aplica os filtros, realiza a individualização dos dígitos
     e e ajusta no formato necessário para alimentar a rede neural. Retorna um np.array com os dígitos
     que compõem o captcha e que servirá de input para rede neural. """

    # Recebe o stream de bytes que representa o captcha e realiza o processamento
    processed_picture = captcha_interpreter(
        captcha_bytes=bites_stream, fund_name=filename
    )

    # Caso o algorítimo tenha processado a figura:
    if processed_picture.size != 0:

        # Separe o captcha em dígitos individuais.
        processed_digits = grab_digits(processed_picture, file_name=filename)

        if processed_digits and len(processed_digits) < 7:

            # Processa para salvar no shape (nx28x28x1) que alimentará a rede neural já treinada
            digits_to_save = []
            for digit in processed_digits:

                digit = resize_to_fit(digit, 28)
                digit = digit / 255
                digit = digit.astype("float32")
                digit = digit.reshape(28, 28, 1)
                digits_to_save.append(digit)

            return np.array(digits_to_save)

    logger.info("Necessário pedir outro captcha")
    return None
