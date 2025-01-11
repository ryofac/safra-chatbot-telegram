# FlufinhoBot - O Chatbot para Agricultura Familiar

**FlufinhoBot** é um chatbot projetado para facilitar o consumo de dados de sistemas de agricultura familiar. Ele opera utilizando a API oficial do Telegram e é alimentado pelos modelos de geração de linguagem **Google Gemini**.

Com o **FlufinhoBot**, agricultores e gestores podem obter informações relevantes sobre produção, consumo, vendas e muito mais de maneira simples e interativa.

## Como Rodar?

1. **Crie o Bot no Telegram**:
   - Utilize o [BotFather](https://core.telegram.org/bots#botfather) para criar um novo bot e obter o token de acesso.

2. **Configuração do Ambiente**:
   - Renomeie o arquivo `dot-env-example` para `.env`.
   - Configure as variáveis de ambiente no arquivo `.env` com os seguintes dados:
     ```env
     BOT_TOKEN=YOUR-BOT-TOKEN # Credenciais do bot
     API_KEY_GEMINI=YOUR-API-KEY-GEMINI # Credenciais GEMINI
     CREDENTIALS_PATH=YOUR-CREDENTIALS-PATH # Credenciais do Firebase (json)
     ```

3. **Inicie o Bot**:
   - Execute o arquivo `main.py` para iniciar a comunicação do bot com a API do Telegram.

