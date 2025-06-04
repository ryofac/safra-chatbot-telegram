import asyncio
import datetime
import json
import logging

import google.generativeai as generai
from google.api_core.exceptions import ResourceExhausted
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

import config
from sensor_source import SensorData, SensorSource

# Enum de estados
CHAT = range(1)

logger = logging.getLogger(__name__)

model = generai.GenerativeModel(config.MODEL_NAME)

chat_sessions = {}

data_source = SensorSource()


def format_external_data(sensor_data: SensorData):
    logging.info(f"DADO DE SENSOR: + {sensor_data}")
    json_sensor_source = sensor_data.__dict__
    json_sensor_source["data_coleta"] = sensor_data.data_coleta.strftime("%Y-%m-%d %H:%M:%S")
    return json_sensor_source


def get_formatted_external_data():
    start_date = datetime.datetime.now()
    end_date = start_date - datetime.timedelta(days=config.LAST_DATA_TIME_IN_DAYS)
    raw_data = data_source.get_data((end_date, start_date))
    sorted_data = sorted(
        raw_data,
        key=lambda x: x.data_coleta,
        reverse=True
    )
    recent_data = sorted_data[:config.DATA_LIMIT]
    formatted_data = [format_external_data(data) for data in recent_data]
    all_data = json.dumps(formatted_data)
    logging.info(f"Dados provenientes dos sensores: {all_data}")
    return all_data


def get_user_message_count(history):
    count = 0
    for message in history:
        if message.role == "user":
            count += 1
    return count


async def start(update, context):
    await update.message.reply_text(
        f"Bem vindo ao {config.BOT_NAME}! \n <b>{config.BOT_DESC}</b>\n Para sair dessa conversa digite: /end",
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
            logger.warning(f"Tentativa {attempt + 1} de enviar mensagem excedeu o tempo limite. Retentando...")
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
                {"role": "model", "parts": config.MODEL_PROMPT},
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

        # Dados formatados provindos da fonte externa
        all_data = get_formatted_external_data()

        prompt = f"""
            Data e hora atuais: {datetime.datetime.now()} 
            Dados atuais dos sensores em json, utilizar somente caso necessário:\n
            {all_data}\n
            Aqui está a mensagem do usuário: {user_message}
            """

        response = await send_message_with_retry(chat_session, prompt)

        await update.message.reply_text(
            response.text,
            parse_mode=ParseMode.MARKDOWN,
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
        logger.info(response.text)

    return CHAT


async def exit(update, context):
    await update.message.reply_text(
        f"""<b>Obrigado por utilizar o {config.BOT_NAME}
        Inicie novamente digitando /start</b> !""",
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
        f"<b> Informações gerais sobre {config.BOT_NAME} </b>\n\n"
        f"* Nome do modelo: {config.MODEL_NAME}\n\n"
        f"* Prompt de geração: {config.MODEL_PROMPT}\n\n"
        f"* Quantidade de mensagens enviadas: {get_user_message_count(chat_session.history)}"
        f"* Quantidade de dados coletados pelos sensores: {int(data_source.get_data_count())}"
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
