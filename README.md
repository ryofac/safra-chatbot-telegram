# SafraBot: Seu monitoramento do ambiente de armazenagem

**SafraBot** é um chatbot projetado para auxiliar no **monitoramento do ambiente de armazenagem de produtos agrícolas**. Ele opera utilizando a API oficial do Telegram e é alimentado pelos modelos de geração de linguagem **Google Gemini**.

Com o **SafraBot**, agricultores e gestores podem obter informações cruciais sobre as **condições de armazenagem**, como dados de temperatura e umidade de silos e armazéns, alertas sobre níveis inadequados, controle de pragas no armazenamento, e recomendações para otimizar a conservação dos produtos colhidos, tudo de maneira simples e interativa.

## Como Rodar?

1.  **Crie o Bot no Telegram**:
    *   Utilize o [BotFather](https://core.telegram.org/bots#botfather) para criar um novo bot e obter o token de acesso.

2.  **Configuração do Ambiente**:
    *   Renomeie o arquivo `dot-env-example` para `.env`.
    *   Configure as variáveis de ambiente no arquivo `.env` com os seguintes dados:
        ```env
        BOT_TOKEN=YOUR-BOT-TOKEN # Credenciais do bot
        API_KEY_GEMINI=YOUR-API-KEY-GEMINI # Credenciais GEMINI
        DATABASE_URL=YOUR-DATABASE-URL # Url do banco de dados
        ```

3.  **Inicie o Bot**:
    *   Execute o arquivo `main.py` para iniciar a comunicação do bot com a API do Telegram.
