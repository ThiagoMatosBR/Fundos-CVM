import os
import sys
import re
import time
import subprocess

import requests
from stem import Signal
from stem.control import Controller

args = ["-h", "-n", "-s"]
error_msg = """\nVocê utilizou opções indisponíveis ou na sequência incorreta!\n """

number_of_files = None


def program_overview():
    options = f"""Argumentos para o programa (atenção para os espaços em branco):
    -h -> Overview sobre o funcionamento.
    -n:number -> número de captchas que serão salvos na pasta (number > 0).
    -s:folder_name -> Salva as imagens na pasta folder_name. Cria a pasta caso não exita.
    
    Exemplo das 3 possibilidades de execução no terminal: 
     1) python3 {__file__} -h 
     [para ajuda]
     
     2) python3 {__file__} -n:1000 -s:Pictures
     [Coleta 1000 captchas e salva na pasta Pictures]

     3) python3 {__file__} -n:10
     [Coleta 10 captchas e salva no subdiretório (default) 'Dataset Pictures'] """

    print(error_msg)
    print(options)
    raise SystemExit


def helper():

    ajuda = """
    Script elaborado para ser executado a partir do terminal. Realiza o download dos captchas
    requisitando o endereço:
    
    "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/RandomTxt.aspx"
    
    Precisa que no mínimo seja fornecido o número (inteiro positivo) de captchas a serem baixados.
    Utiliza o TOR como proxy (protocolo SOCKS) nas portas 9050 e 9051 para anonimizar os requests
    e, em caso de erros devido a quantidade de requests excessivos (erro 403) ou timeout, faz a rotação 
    de proxy, estabelecendo um novo circuito para o tor. 
    
    Se o tor não estiver ouvindo na porta 9050 não irá funcionar. Mais detalhes em: https://www.torproject.org/
    
    Para mais detalhes sobre rotação de proxy com stem/tor: https://stem.torproject.org/index.html 

    O estabelecimento de novos circuitos pode levar até 10s. No máximo 20 tentativas de retomada do download,
    do contrário interrompe a execução.

    Caso não seja fornecido local específico para salvar os arquivos, cria o subdiretório Dataset Pictures.
    Realiza o log dos eventos do download no arquivo log_download_captchas.txt e mesmo diretório em que o
    script está salvo.\n"""

    print(ajuda)
    raise SystemExit


def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="jarvis")
        controller.signal(Signal.NEWNYM)


def tor_check():
    checker = subprocess.run(
        "lsof -iTCP -sTCP:LISTEN | grep tor", shell=True, capture_output=True, text=True
    )

    return checker.returncode


def progress_bar(n, elapsed_time):

    total = int(number_of_files)
    width = 50
    percent = n / total
    left = int(width * percent)
    right = width - left - 1
    eta = elapsed_time * (total - n)
    print(
        "\r[",
        "-" * left,
        ">",
        " " * right,
        "]",
        f" {100 * percent:.1f}%",
        f"    ETA: {eta:.1f}s \b",
        sep="",
        end="",
        flush=True,
    )


try:
    pattern = re.compile(r"-n:(\d+)")
    candidates = pattern.search(sys.argv[1])

    if candidates:
        number_of_files = candidates.group().split(":")[1]

except IndexError:
    program_overview()


try:
    pattern_dir = re.compile(r"-s:(\w+)")
    candidates_dir = pattern_dir.search(sys.argv[2])

    if candidates_dir:
        destin_dir = candidates_dir.group().split(":")[1]
    else:
        destin_dir = "Dataset Pictures"

except IndexError:
    destin_dir = "Dataset Pictures"


if len(sys.argv) == 2 and sys.argv[1] == args[0]:
    helper()

elif number_of_files:
    url = "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/RandomTxt.aspx"
    proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

    if tor_check():
        print(
            "\nO TOR não está ouvindo nas portas 9050 e 9051. Favor instanciar o TOR.",
            flush=True,
        )
        raise SystemExit

    if not os.path.isdir(destin_dir):
        os.mkdir(destin_dir)

    path = os.path.join(os.getcwd(), destin_dir)

    loop_breaker = 0
    with open("log_download_captchas.txt", "w") as file_object:
        print("Log de Eventos salvo em arquivo. Evolução do download abaixo:\n")
        for i in range(1, int(number_of_files) + 1):

            if loop_breaker > 20:
                print("Número máximo de rotações de iP excedido.", file=file_object)
                break

            try:
                start = time.perf_counter()
                site = requests.get(url, timeout=6, proxies=proxies)
                file_name = os.path.join(path, f"Picture_{i}.png")

                if site.status_code == 200:

                    with open(file_name, "wb") as f:
                        f.write(site.content)
                        print(
                            f"Realizado o download: {file_name} com sucesso.",
                            file=file_object,
                        )

                    progress_bar(i, elapsed_time=(time.perf_counter() - start))

                else:
                    print(
                        f"Erro na requisição do site. Status code: {site.status_code}",
                        file=file_object,
                    )
                    renew_tor_ip()
                    time.sleep(10)
                    loop_breaker += 1

            except Exception as other_error:
                print("Ocorreu o seguinte erro: ", other_error, file=file_object)
                renew_tor_ip()
                time.sleep(10)
                loop_breaker += 1

else:
    program_overview()
