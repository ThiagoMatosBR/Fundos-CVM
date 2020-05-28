import datetime
import sqlite3
import logging
import logging.config

from bs4 import BeautifulSoup

# Configura o display e salvamento de logs
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("database")


class Write_to_SQLlite(object):
    """Insere os dados do site da CVM numa base de dados SQLlite."""

    def __init__(self, data_base_name: str):

        self.conn = sqlite3.connect(
            data_base_name, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.c = self.conn.cursor()

        logger.info("Conexão com o banco de dados estabelecida com sucesso.")

    def _create_table(self, CNPJ_fund: str):
        """Cria a tabela no banco de dados caso não exista. 
        
        - Obs: Nome da tabela: table_CNPJ(somente dígitos). """

        self.CNPJ = "".join([i for i in CNPJ_fund if i.isdigit()])

        # Caso a tabela não exita, opto por "criá-la" com uma data no passado
        # Recurso para reaproveitamento de código
        self.last_update = datetime.date(1969, 12, 31)

        try:
            self.c.execute(
                f"""CREATE TABLE IF NOT EXISTS table_{self.CNPJ}(Data DATE, Quota REAL, Captação_dia REAL,
                Resgate_dia REAL, Patrimônio_Líquido REAL, Total_da_Carteira REAL, No_de_Cotistas INTEGER)"""
            )
            logger.info(f"Criada a tabela {self.CNPJ} no banco de dados.")
        except Exception as err2:
            logger.error(
                f"Ocorreu o seguinte erro ao tentar criar a tabela {CNPJ_fund}: {err2}."
            )

    def _data_entry(self, data: tuple):
        """Definições: Insere no banco de dados as informações processadas por _convert_data()

        - CNPJ: CNPJ do fundo no formato string, correspondente a tabela no banco de dados
        - data: tupla de dados que se deseja inserir no banco de dados """

        # self.CNPJ = "".join([i for i in CNPJ_fund if i.isdigit()])

        with self.conn:

            try:
                self.c.execute(
                    f"""INSERT INTO table_{self.CNPJ} (data, Quota, Captação_dia, Resgate_dia, Patrimônio_Líquido,
                Total_da_Carteira, No_de_Cotistas) VALUES (?,?,?,?,?,?,?)""",
                    data,
                )
            except Exception as err:
                logger.exception(
                    f"Erro ao tentar acessar registar o fundo na base de dados {err}."
                )

    def _convert_data(self, n: str, month: str, i):

        "Converte datas para datetime.date e dados numéricos para float"
        if i == 0:

            date_converted = datetime.datetime.strptime(
                f"{n}/{month}", "%d/%m/%Y"
            ).date()

            return date_converted

        try:
            n_converted = float(n.replace(".", "").replace(",", "."))
            return n_converted
        except ValueError:
            return n

    def feed_SQL_DB(self, table, month: str):
        """Definição:
         - table: tabela em formato html, processa as colunas e linhas de interesse.
         - month: mês e ano extraídos da página, no formato mm/yyyy
         - Data são convertidas para o formato datetime.date.
         - Automaticamente elimina linhas em branco.
         - Compara a data disponível com a data de última atulização do banco de dados e grava
        no banco caso o dado seja inédito."""

        soup = BeautifulSoup(table, "lxml")
        table_rows = soup.find_all("tr")

        for row in table_rows[1:]:
            # Coleta o dia e converte para datetime.date
            date_availabe = self._convert_data(row.find("td").text, month, 0)

            if date_availabe > self.last_update:

                elements = row.find_all("td")[:-1]

                # Caso não tenha o dado de valor da cota, não me serve
                if elements[1].text == "\xa0":
                    continue
                else:
                    data = (element.text.replace("\xa0", "") for element in elements)

                    final_result = tuple(
                        self._convert_data(item, month, i)
                        for i, item in enumerate(data)
                    )

                    self._data_entry(final_result)

    def close_connection(self):

        self.c.close()
        self.conn.close()
        logger.info("Encerrada a conexão com o banco de dados.")

    def read_from_DB(self, CNPJ_fund: str):
        """Faz um query específica dentro da tabela, precisa ser programado a depender
        da funcionalidade que se desejar. """

        CNPJ_fund = "".join([i for i in CNPJ_fund if i.isdigit()])

        table_name = f"table_{CNPJ_fund}"

        # A query de leitura fica sob sua responsabilidade
        self.c.execute(f"""SELECT * FROM {table_name} WHERE Quota = '';""")

        return self.c.fetchall()

    def get_last_update(self, CNPJ_fund: str):
        """Realiza uma query na base de dados SQLlite para obter a data mais recente
        de atualização. Cria a tabela com os dados do fundo caso o mesmo não exista."""

        self.CNPJ = "".join([i for i in CNPJ_fund if i.isdigit()])

        table_name = f"table_{self.CNPJ}"

        try:
            self.c.execute(
                f"""SELECT Data from {table_name} ORDER by Data DESC LIMIT 1;"""
            )
            self.last_update, = self.c.fetchall()[0]

        except sqlite3.OperationalError:

            self._create_table(CNPJ_fund)

        return None
