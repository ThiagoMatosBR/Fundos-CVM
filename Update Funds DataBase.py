import os
import json
import logging
import logging.config

from tensorflow.keras.models import load_model
from selenium import webdriver
import numpy as np

# Mudando para o diretório dos módulos
os.chdir(os.path.dirname(__file__))

from Captcha_Processor import digits_extractor
from CVM_WebPage import CVM_Page
from Write_on_DB import Write_to_SQLlite


# Configura o display e salvamento de logs e desabilita os logs do tensor flow
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logging.getLogger("tensorflow").setLevel(logging.ERROR)
logger = logging.getLogger("main")

# Carregando a rede neural
model = load_model("Captcha_model.h5", compile=False)

# Realizando a leitura da lista de fundos.
with open("fundos.json") as json_file:
    fundos = json.load(json_file)

keys = (key for key, _ in fundos.items())

# Configurando o proxy e headless mode
PROXY = "socks5://127.0.0.1:9050"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--proxy-server={PROXY}")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

# Conectando-se a base de dados SQLlite
SQL_DB = Write_to_SQLlite("Fundos de Investimento2.db")

# Percorrendo os fundos disponíveis:
for key in keys:

    browser = webdriver.Chrome(options=chrome_options)
    CVM = CVM_Page(driver=browser)

    logger.info(f"Atualizando dados do fundo: {fundos[key]}.")
    CVM.go()
    CVM.find_frame.go_to_frame()

    max_tries = 7
    tries = 0

    while tries < max_tries:
        tries += 1
        captcha = digits_extractor(
            bites_stream=CVM.find_captcha.grab_captcha(), filename=fundos[key]
        )

        if captcha is not None:
            interpreted_captcha = "".join(
                [str(np.argmax(result)) for result in model.predict(captcha)]
            )

        else:
            CVM.ask_new_captcha.click()
            continue

        CVM.CNPJ.input_text(text=key)
        CVM.captcha_field.input_text(text=interpreted_captcha)
        CVM.log_in_btn.click()

        # Verificando se tive sucesso em logar:
        if CVM.select_fund(fund_id=key).is_present():
            break

    if tries >= max_tries:
        logger.warning(
            f"Não conseguimos logar na tentativa de atualização do fundo: {fundos[key]}"
        )
        CVM.close_browser()
        continue

    logger.info(f"Número de tentativas de log no fundo {fundos[key]}: {tries}.")

    # Clicando no fundo de interesse:
    CVM.select_fund(fund_id=key).click()

    # Indo para a tabela de interesse:
    CVM.go_to_tables.click()

    # Obtendo os meses disponíveis para aquele dado fundo:
    all_months = CVM.select_months.months_available()

    # Obtendo uma lista com os dois últimos meses disponíveis:
    list_of_months = [
        month.strip() for month in all_months.split("\n") if month.strip() is not ""
    ][0:2]

    # Conectando-se a tabela daquele referido fundo:
    SQL_DB.get_last_update(CNPJ_fund=key)

    for month in list_of_months:
        CVM.select_months.pick_month(month_year=month)
        table_data = CVM.table.fetch_data()
        SQL_DB.feed_SQL_DB(table_data, month)

    logger.info(f"Base de dados atualizada com dados do fundo: {fundos[key]}")
    CVM.close_browser()

CVM.quit_browser()
SQL_DB.close_connection()

logger.info("Fim da rotina de atualização dos fundos.")
