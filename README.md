[![HitCount](http://hits.dwyl.com/ThiagoMatosBR/https://githubcom/ThiagoMatosBR/Fundos-CVMgit.svg)](http://hits.dwyl.com/ThiagoMatosBR/https://githubcom/ThiagoMatosBR/Fundos-CVMgit)
# Descrição
___
### Objetivo:
Obter informações dos fundos de investimento listados na CVM. A consulta é realizada a partir do CNPJ dos fundos e são obtidos dados como: valor diário da quota, captção dia, resgate do dia, número de cotistas. Para o acesso a tabela com as informações de interesse é necessário informar o número que aparece em uma imagem de captcha randômica. Desta forma, foi preciso programar uma rede neural que resolvesse captchas semelhantes.

#### Exemplos de Captchas que são resolvidos:
![](Build%20Dataset/Labeled%20Pictures/13572.png) ![](Build%20Dataset/Labeled%20Pictures/3233.png) ![](Build%20Dataset/Labeled%20Pictures/8516.png) ![](Build%20Dataset/Labeled%20Pictures/92132.png) ![](Build%20Dataset/Labeled%20Pictures/6553.png)

### O repositório está dividido em:

**1) Scripts na pasta Build Dataset**:
 * ***Build Dataset.py*** utiliza o funções do módulo Captcha_processor para processar os captchas salvos na pasta Labeled Captchas. O resultado do script são os np.arrays que serão utilizados no treinamento da rede neural.
 * ***Captcha_downloader.py*** é um script pensado para ser executado via terminal e que faz o download dos captchas. Utiliza o tor para anonimizar os requests e cria um log em txt com os captchas baixados.
 * A pasta ***Labeled Pictures*** contém exemplos dos captchas que a rede neural processa. Estes captchas foram identificados manualmente.
 
**2) Scripts na pasta Rede Neural**:
 * ***Captcha_after_drop_ajusts_+_Keras.ipynb*** contém os detalhes da arquitetura de rede neural convolucional que foi utilizada para interpretação dos dígitos dos captchas. 

**3) Scripts em Fundos-CVM**:
 * ***BasePage.py***: contém a classe que define métodos relacionados a navegação na página e a url de acesso aos fundos.
 * ***CVM_WebPage.py***: classe que contém diversos métodos descrevem a estrutura das diversas páginas que são acessadas
 * ***BaseElements.py***: classe com as diversas ações realizadas na página, como clicar em um link, selecionar informações em um picklist, selecionar o captcha, etc.
 * ***Captcha_processor.py***: módulo com diversas funções utilizadas no processamento dos captchas. Principal módulo, pois é utilizado na contrução do data-set utilizado para treinar a rede neural e também no tratamento dos captchas durante o acesso ao site.
 * ***Captcha_model.h5***: arquivo em fomato h5 e que contém os pesos e estutura da rede neural treinada. É o modelo estuturado que é importado para resolver os captchas que são processados pelas funções do módulo Captcha_processor.
 * ***fundos.json***: os fundos cujas informações serão coletadas no site da CVM.
 * ***Write_on_DB.py***: classe que acessa / cria / modifica uma base de dados SQLlite, adicionando as informações dos fundos listados em fundos.json.
 * ***Update Funds DataBase.py***: script que executa o seguinte workflow: acessa o site da CVM (utilizando IP anônimo) - coleta o captcha - resolve o captcha com a rede neural - insere o CNPJ do fundo de interesse e loga na página - se dirige a seção com "Dados Diários" - coleta as informações como valor da quota, captação, total de cotistas, etc - caso as informações sejam inéditas, alimenta o banco de dados SQL. Esse fluxo é repetido para cada um dos fundos de interesse. 
 * ***logging.conf***: arquivo de configuração importado pelos vários scripts e utilizado para configurar os logs.

Para melhor entendimento de eventuais erros / exceptions, as ações na página, acesso ao banco de dados e processamento dos captchas são logados no stdout ou em arquivo .log.
___
