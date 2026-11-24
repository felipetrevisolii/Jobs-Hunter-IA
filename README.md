# Jobs Hunter IA

**Automação de busca, filtragem e monitoramento de oportunidades em Tecnologia da Informação.**

Projeto desenvolvido em Python para coletar vagas publicadas em diferentes plataformas, avaliar sua relevância, evitar registros duplicados e organizar as oportunidades para acompanhamento.

O sistema utiliza regras configuráveis de filtragem e pontuação para priorizar vagas de acordo com o perfil profissional desejado.

> Status: primeira versão pública disponível no GitHub.

## Visão geral

O Jobs Hunter IA automatiza etapas repetitivas da procura por oportunidades profissionais.

O fluxo reúne vagas, aplica critérios de seleção e encaminha resultados relevantes para acompanhamento.

O projeto não realiza candidaturas automáticas, não envia currículos e não substitui a avaliação humana das oportunidades.

## Funcionalidades

- Coleta automatizada de vagas em diferentes fontes.
- Filtragem por cargo, área profissional e localização.
- Busca de oportunidades remotas no Brasil.
- Identificação e tratamento de oportunidades de estágio.
- Critérios salariais configuráveis para empregos.
- Avaliação e priorização de vagas por relevância.
- Identificação de vagas já processadas utilizando SQLite.
- Registro de oportunidades no Google Sheets.
- Notificações de vagas via Telegram.
- Logs de execução e tratamento de erros.
- Execução programada pelo Agendador de Tarefas do Windows.

As integrações externas dependem de configuração e disponibilidade dos respectivos serviços.

## Áreas profissionais

O projeto foi desenvolvido com foco nas seguintes áreas:

- Automação e Inteligência Artificial
- Análise de Dados
- Business Intelligence (BI)
- Desenvolvimento de Software

Vagas de suporte em TI também podem ser analisadas como oportunidades complementares.

## Critérios de busca

A configuração de exemplo contempla:

- Vagas remotas em território brasileiro.
- Vagas presenciais e híbridas nas cidades de Campinas, Valinhos, Hortolândia e Vinhedo.
- Empregos com critérios salariais configuráveis.
- Estágios avaliados separadamente do piso salarial de empregos.

As regras de seleção podem ser ajustadas por variáveis de ambiente e pelo código do projeto.

## Tecnologias

| Tecnologia | Aplicação |
| --- | --- |
| Python | Automação e regras de processamento |
| Requests | Requisições HTTP |
| Beautiful Soup | Extração de informações de páginas |
| SQLite | Persistência e controle de duplicidades |
| Google Sheets API | Registro e acompanhamento das vagas |
| Telegram Bot API | Notificações |
| python-dotenv | Configuração por variáveis de ambiente |
| unittest | Testes automatizados |
| Windows Task Scheduler | Agendamento local |

## Estrutura do projeto

    jobs-hunter-ia/
    |-- main.py
    |-- areas_ti.py
    |-- services/
    |   |-- avaliador_perfil.py
    |   |-- banco.py
    |   |-- filtro.py
    |   |-- filtro_novas_oportunidades.py
    |   |-- fluxo_empregos_ti.py
    |   |-- logger_config.py
    |   `-- telegram_sender.py
    |-- scrapers/
    |   |-- estrutura.py
    |   |-- empregacampinas.py
    |   |-- infojobs.py
    |   `-- trabalhabrasil.py
    |-- scripts/
    |   `-- rotacionar_log_agendador.py
    |-- tests/
    |   |-- testes_ti.py
    |   `-- testar_etapas_ti.py
    |-- requirements.txt
    |-- rodar_job_hunter.bat
    |-- .env.example
    |-- .gitignore
    `-- README.md

## Instalação

### 1. Requisitos

- Python instalado no Windows.
- Acesso à internet para consultar as fontes de vagas.
- Credenciais próprias para as integrações que serão utilizadas.

### 2. Criar um ambiente virtual

No PowerShell, dentro da pasta do projeto:

    py -m venv .venv

### 3. Instalar as dependências

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

### 4. Configurar as variáveis

Crie um arquivo `.env` a partir do modelo:

    Copy-Item .env.example .env

Preencha as configurações necessárias para seu ambiente.

O arquivo de exemplo não contém tokens ou identificadores privados.

As integrações com Google Sheets e Telegram exigem credenciais próprias. O arquivo JSON de autenticação do Google, quando utilizado, deve permanecer privado.

**Atenção:** a presença de `MODO_TESTE=true` no arquivo de exemplo não garante, por si só, que a execução seja livre de efeitos externos. Esse comportamento ainda precisa ser validado na versão pública.

### 5. Execução

Depois de configurar as integrações e validar o ambiente, o ponto de entrada é:

    py main.py

O arquivo `rodar_job_hunter.bat` foi preparado para utilização no Windows e inclui registro de execução.

Não execute o programa com credenciais reais sem antes verificar as configurações e o comportamento esperado.

## Testes automatizados

Para executar os testes unitários:

    py -m unittest -v tests.testes_ti

Para executar os testes adicionais:

    py -m tests.testar_etapas_ti

Os testes atuais cobrem regras de filtragem e classificação de oportunidades.

A integração completa com plataformas externas depende de testes adicionais e de acesso aos serviços correspondentes.

## Logs

O projeto utiliza registros para auxiliar na identificação de falhas e no acompanhamento das execuções.

O logging do Python utiliza rotação de arquivos.

O inicializador do Windows possui uma rotina complementar para limitar o histórico do log do Agendador.

Os logs locais não devem ser incluídos no repositório público.

## Segurança e privacidade

Os seguintes arquivos e informações devem permanecer fora do GitHub:

- Arquivo `.env` com credenciais reais.
- Tokens e identificadores privados do Telegram.
- Credenciais de autenticação do Google.
- Currículos e documentos pessoais.
- Bancos de dados locais com histórico de vagas.
- Logs de produção e arquivos de backup.

O projeto possui um `.gitignore` para ajudar a proteger esses arquivos.

Antes de futuras atualizações, revise os arquivos para evitar a publicação de credenciais ou informações privadas.

## Limitações

A extração de vagas depende da estrutura e da disponibilidade dos sites consultados. Alterações nas páginas, mecanismos de proteção ou indisponibilidade dos serviços podem exigir manutenção dos coletores.

A pontuação das vagas representa critérios de relevância configurados no projeto e não garante adequação profissional nem contratação.

A execução automatizada deve respeitar as condições de uso das fontes consultadas.

## Estado do desenvolvimento

A versão de produção já foi utilizada para buscas automatizadas e registro de oportunidades.

A versão pública está disponível no GitHub. Os testes offline foram aprovados; as integrações externas dependem de configuração no ambiente de execução.

## Objetivo do projeto

Demonstrar competências práticas em Python, automação, integração de APIs, processamento de dados, persistência de informações, testes e organização de software.

O projeto foi criado para resolver um problema real: reduzir o trabalho manual necessário para identificar e acompanhar oportunidades relevantes em Tecnologia da Informação.