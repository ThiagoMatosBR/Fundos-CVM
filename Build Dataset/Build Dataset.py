import os
import concurrent.futures
import logging
import logging.config
import sys

sys.path.append(
    "/Users/Thiago/Desktop/Python Homework/Estudos Web Scrapping/Fundos CVM"
)

import numpy as np
from cv2 import cv2
from Captcha_processor import captcha_interpreter, grab_digits, resize_to_fit

"""Constrói o dataset que será empregado no treinamento da rede neural. Utiliza-se de 
multi-threading para processar diversas imagens de forma concorrente.

ATENÇÃO Uso intensivo de memória (devido à construção da lista com arrays contendo cada um dos dígitos)
caso o número de captchas seja muito grande, pode ser necessário rodar o script em bateladas

1) Faz a leitura dos captchas com os dígitos já identificados na pasta Labeled Pictures.
2) Para cada um dos arquivos da pasta, aplica os filtros e o script de controle de qualidade
(captcha_interpreter) do módulo Captcha_processor.
3) Caso a imagem processada tenha apresentado qualidade, isola cada um dos dígitos da imagem 
e redimensiona-os para o shape de array que irá alimentar a rede neural (28,28)
4) Simultaneamente, salva na pasta Processed Digits os dígitos processados e compõe os arrays
correspondentes aos dígitos processados e aos labels para estes dígitos.
5) Ao final, salva o dataset em formato npz (array numpy), sendo um arquivo com cada um dos 
dígitos processados (pictures_x_data.npz) e um outro (labels_y_data.npz) com cada um dos labels.

Os arquivos pictures_x_data.npz e labels_y_data serão importados durante o treinamento da
rede neural."""

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger("auxiliar")

logger.info("Iniciando o tratamento das imagens.")

path_to_pictures = "Labeled Pictures"
path_processed_pictures = "Processed Digits"

# Coletando a lista de imagens já identificadas e disponíveis no diretório
list_of_pictures = (
    entry.path for entry in os.scandir(path_to_pictures) if entry.name.endswith("png")
)

if not os.path.isdir(path_processed_pictures):
    os.mkdir(path_processed_pictures)


def _digits_extractor(picture: str):

    # Processando cada uma das figuras:
    processed_picture = captcha_interpreter(file_name=picture)

    # Obtendo o label, somente o número sem a extensão .png
    picture_label = picture.split("/")[-1].split(".")[0]

    # Caso o script tenha processado a figura:
    if processed_picture.size != 0:

        # Colete cada um dos dígitos
        processed_digits = grab_digits(processed_picture, picture)

        # Se conseguir processar dígitos e o número de dígitos corresponder ao label:
        if processed_digits and len(processed_digits) == len(picture_label):

            # Processa para salvar no shape (28x28) que alimentará a rede neural
            digits_to_save = [
                resize_to_fit(element, 28) for element in processed_digits
            ]

            return (digits_to_save, list(map(int, picture_label)))

    return None


images, labels = [], []

#Multithreading mostrou performace semelhante ao multiprocessing em CPU com 4 cores
#Optado pelo multithreading pela facilidade de logar.
with concurrent.futures.ThreadPoolExecutor() as executor:
    resultados = (executor.submit(_digits_extractor, pic) for pic in list_of_pictures)

    for f in concurrent.futures.as_completed(resultados):
        
        #Constrói uma lista com arrays correspondendo ao dígitos e 
        # uma lista com cada um dos labels
        try:
            imagem, label = f.result()

            images = images + imagem
            labels = labels + label
        except Exception:
            pass

# Convertendo as imagens e labels para array numpy
images = np.array(images)
labels = np.array(labels)

# Salvando as imagens e labels em arquivo npz para posterior uso na rede neural
np.savez("pictures_x_data", images)
np.savez("labels_y_data", labels)

logger.info("Tratamento das imagens concluído.")
