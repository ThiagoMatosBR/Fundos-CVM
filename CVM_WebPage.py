from BasePage import Base_page
from BaseElements import Base_Elements
from selenium.webdriver.common.by import By


class CVM_Page(Base_page):
    """Classe com os diversos elementos que compõem as páginas de interesse."""

    @property
    def find_frame(self):

        locator = (By.XPATH, '//frame[@name="Main"]')

        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def find_captcha(self):

        locator = (By.TAG_NAME, "img")
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def CNPJ(self):

        locator = (By.XPATH, '//input[@name="txtCNPJNome"]')

        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def captcha_field(self):

        locator = (By.XPATH, '//input[@name="numRandom"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def log_in_btn(self):

        locator = (By.XPATH, '//input[@name="btnContinuar"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def log_in_error(self):

        locator = (By.XPATH, '//span[@id="lblMsg"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def ask_new_captcha(self):

        locator = (By.XPATH, '//a[@id="lkNovoRandom"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    def select_fund(self, fund_id: str):

        locator = (By.XPATH, f'//a[contains(text(), "{fund_id}")]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def go_to_tables(self):

        locator = (By.XPATH, '//a[@id="Hyperlink2"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def select_months(self):

        locator = (By.XPATH, '//select[@id="ddComptc"]')
        return Base_Elements(self.driver, locator[0], locator[1])

    @property
    def table(self):

        locator = (By.XPATH, '//table[@id="dgDocDiario"]')
        return Base_Elements(self.driver, locator[0], locator[1])
