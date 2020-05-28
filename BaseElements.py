import logging
import logging.config

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.common.exceptions import TimeoutException

# Configura o display e salvamento de logs
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("webpage")


class Base_Elements(object):
    """Ações que serão realizadas na página """

    def __init__(self, driver, by, value):

        self.driver = driver
        self.by = by
        self.value = value
        self.locator = (self.by, self.value)

        self.web_element = None

    def go_to_frame(self):
        """ Na página de acesso, muda para o frame principal da página."""
        try:
            WebDriverWait(self.driver, timeout=120).until(
                EC.frame_to_be_available_and_switch_to_it(locator=self.locator)
            )
        except TimeoutException:
            logger.exception("Timeout error ao mudar de frame.")
        except NoSuchElementException:
            logger.exception("Frame não existe na página principal da CVM")

        return None

    def grab_captcha(self):
        """Coleta, na página de acesso, o captcha em stream de bytes."""
        try:
            self.web_element = WebDriverWait(self.driver, timeout=10).until(
                EC.presence_of_element_located(locator=self.locator)
            )
            captcha_bytes = self.web_element.screenshot_as_png
        except NoSuchElementException:

            logger.exception("Captcha não disponível")

        except TimeoutException:
            logger.exception("Captcha não carregou a tempo - Timeout")

        return captcha_bytes

    def input_text(self, text):

        self.web_element = WebDriverWait(self.driver, timeout=5).until(
            EC.visibility_of_element_located(locator=self.locator)
        )

        self.web_element.clear()
        self.web_element.send_keys(text)

        return None

    def click(self):

        try:
            self.web_element = WebDriverWait(self.driver, timeout=45).until(
                EC.element_to_be_clickable(locator=self.locator)
            )

            self.web_element.click()
        except NoSuchElementException:
            logger.exception("Elemento clicável não estava disponível.")
        except TimeoutException:
            logger.exception("Elemento clicável não carregou a tempo.")

        return None

    def is_present(self):
        """Confirma se o fundo selecionado está de fato presente na página. Esta é a forma
        de assegurar que conseguiu logar com sucesso. """

        try:
            self.web_element = WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located(locator=self.locator)
            )

            return True
        except (NoSuchElementException, WebDriverException):
            return False

    def months_available(self):
        """Verifica no picklist da CVM quais são os meses disponíveis para acesso. """
        try:
            self.web_element = WebDriverWait(self.driver, timeout=30).until(
                EC.presence_of_element_located(locator=self.locator)
            )
        except NoSuchElementException:
            logger.exception("Os picklist de meses não estava disponível.")
        except TimeoutException:
            logger.exception("O picklist de meses não carregou a tempo - Timeout.")

        return self.web_element.text

    def pick_month(self, month_year: str):
        """Dado um mês informado, aplica este mês no picklist da CVM. """

        self.web_element = WebDriverWait(self.driver, timeout=30).until(
            EC.element_to_be_clickable(locator=self.locator)
        )

        self.web_element.send_keys(month_year)

    def fetch_data(self):
        """Coleta a tabela com os dados diários do fundo de interesse."""
        try:
            self.web_element = WebDriverWait(self.driver, timeout=30).until(
                EC.presence_of_element_located(locator=self.locator)
            )
        except NoSuchElementException:
            logger.exception(
                "Houve mudança no código fonte do site - tabela de dados mensais"
            )

        except TimeoutException:
            logger.exception("Tabela de dados mensais não carregou a tempo - Timeout.")

        return self.web_element.get_attribute("innerHTML")
