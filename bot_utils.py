import asyncio
import datetime
import json
import logging
import time

import google.generativeai as generai
from google.api_core.exceptions import ResourceExhausted
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

import config
from config import MODEL_NAME, MODEL_PROMPT
from sensor_source import SensorData, SensorSource

# Enum de estados
CHAT, REQUEST_IMAGE, PROCESSING_IMAGE = range(3)


logger = logging.getLogger(__name__)

model = generai.GenerativeModel(config.MODEL_NAME)

chat_sessions = {}

data_source = SensorSource("./external/cred.json")


def format_external_data(sensor_data: SensorData):
    logging.info(f"DADO DE SENSOR: + {sensor_data}")
    json_sensor_source = sensor_data.__dict__
    json_sensor_source["data_coleta"] = sensor_data.data_coleta.timestamp()
    return json_sensor_source


def get_user_message_count(history):
    count = 0
    for message in history:
        if message.role == "user":
            count += 1
    return count


async def start(update, context):
    await update.message.reply_text(
        "Bem vindo ao FlufinhoBot! \n <b>O seu amigo de irrigação!</b>\n Para sair dessa conversa digite: /end",
        parse_mode=ParseMode.HTML,
    )
    return CHAT


async def error_handler(update, context):
    logger.error(msg="Ocorreu um erro crítico:", exc_info=context.error)
    await update.message.reply_text("Ocorreu um erro. Tente novamente mais tarde")


async def send_message_with_retry(chat_session, prompt, retries=3):
    for attempt in range(retries):
        try:
            response = await asyncio.wait_for(chat_session.send_message_async(prompt), timeout=10)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Tentativa {attempt + 1} de enviar mensagem excedeu o tempo limite. Reintentando...")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem na tentativa {attempt + 1}: {e}", exc_info=True)
        except ResourceExhausted as err:
            await chat_session.message.reply_text(
                f"Limite de quota alcançado : {err}",
            )

    raise RuntimeError("Falha ao enviar mensagem após várias tentativas.")


def get_or_create_chat_session(user_id):
    chat_session = chat_sessions.get(user_id)
    if chat_session is None:
        chat_session = model.start_chat(
            history=[
                {"role": "model", "parts": MODEL_PROMPT},
                {"role": "model", "parts": "Você vai receber dados de sensores a cada mensagem do usuário"},
            ]
        )
        chat_sessions[user_id] = chat_session
    return chat_session


async def chat(update, context):
    user_id = update.message.from_user.id
    chat_session = get_or_create_chat_session(user_id)
    try:
        user_message = update.message.text.strip() if update.message.text else None

        if not user_message:
            await update.message.reply_text(
                "Desculpe, não entendi sua mensagem. Por favor, tente novamente.",
                parse_mode=ParseMode.HTML,
            )
            return CHAT

        await update.message.reply_text(
            "<b>Gerando sua resposta...</b>",
            parse_mode=ParseMode.HTML,
        )
        start_time = time.time()

        start_date = datetime.datetime.now()
        end_date = start_date - datetime.timedelta(days=5000)

        raw_data = data_source.get_data((end_date, start_date))

        all_data = json.dumps([format_external_data(data) for data in raw_data])

        logging.info(all_data)

        prompt = f"""\n Perfira respostas curtas, dados atuais dos sensores em json:\n
        {all_data}\n
        Aqui está a mensagem do usuário: {user_message}"""

        response = await send_message_with_retry(chat_session, prompt)
        elapsed_time = time.time() - start_time

        # logger.info(f"Mensagem enviada: {user_message}")
        # logger.info(f"Mensagem recebida: {response.text}")
        # logger.info(f"Tempo de resposta do modelo: {elapsed_time:.2f} segundos")

        await update.message.reply_text(
            response.text,
            parse_mode=ParseMode.MARKDOWN,
        )

        await update.message.reply_text(
            f"Tempo de resposta do modelo: {elapsed_time:.2f} segundos",
        )

    except Exception as e:
        logger.error(
            f"Ocorreu um erro ao gerar a resposta: {e}",
            exc_info=True,
        )
        await update.message.reply_text(
            "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde.",
            parse_mode=ParseMode.HTML,
        )
        logger.info(chat_sessions)

    return CHAT


async def exit(update, context):
    await update.message.reply_text(
        "<b>Obrigado por utilizar o FlufinhoBot \n Para mais informações sobre o monitoramente digite /start</b>",
        parse_mode=ParseMode.HTML,
    )

    chat_sessions.pop(update.message.from_user.id, None)

    return ConversationHandler.END


async def get_info(update, context):
    chat_session = chat_sessions.get(update.message.from_user.id, None)

    if not chat_session:
        await update.message.reply_text("Não consegui obter informações de conversa, converse comigo primeiro")
        return CHAT

    data = (
        "<b> Informações gerais sobre o FlufinhoBot </b>\n\n"
        f"* Nome do modelo: {MODEL_NAME}\n\n"
        f"* Prompt de geração: {MODEL_PROMPT}\n\n"
        f"* Quantidade de mensagens enviadas: {get_user_message_count(chat_session.history)}"
        f"* Quantidade de dados coletados pelos sensores: {data_source.get_data_count()}"
    )

    await update.message.reply_text(data, parse_mode=ParseMode.HTML)
    await update.message.reply_text("Aguarde, obtendo informações sobre nossa conversa...")

    try:
        chat_overview_response = await send_message_with_retry(
            chat_session, "Gere um historico da nossa conversa, em topicos"
        )
        await update.message.reply_text(chat_overview_response.text, parse_mode=ParseMode.HTML)

    except Exception as e:
        print(e)
        await update.message.reply_text(
            "Não consegui obter informações sobre o histórico da nossa conversa mas sei que foi bem legal"
        )
