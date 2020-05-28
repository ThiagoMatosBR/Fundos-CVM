class Base_page(object):
    """Classe que define os métodos relacionados ao manejo da página. """

    url = "https://cvmweb.cvm.gov.br/swb/default.asp?sg_sistema=fundosreg"

    def __init__(self, driver):

        self.driver = driver

    def go(self):
        self.driver.get(self.url)

    def close_browser(self):
        self.driver.close()

    def quit_browser(self):
        self.driver.quit()
