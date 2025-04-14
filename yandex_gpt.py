import aiohttp
import os
import logging
from dotenv import load_dotenv

load_dotenv()
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

async def get_iam_token(oauth_token: str) -> str:
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    data = {
        "yandexPassportOauthToken": oauth_token
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            result = await resp.json()
            return result.get("iamToken")

category_mapping = {
    "Бизнес": "business",
    "Саморазвитие": "self_growth",
    "Любовь к себе": "self_love",
    "Спорт": "sport"
}

async def generate_yandex_gpt_quote(category: str) -> str:
    prompts = {
        "business": "мотивационная цитата про бизнес",
        "self_growth": "мотивационная цитата про саморазвитие",
        "self_love": "мотивационная цитата про любовь к себе",
        "sport": "мотивационная цитата про спорт"
    }

    mapped_category = category_mapping.get(category)
    prompt_text = prompts.get(mapped_category, "мотивационная цитата на любую тему")

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    try:
        iam_token = await get_iam_token(YANDEX_OAUTH_TOKEN)

        headers = {
            "Authorization": f"Bearer {iam_token}",
            "Content-Type": "application/json"
        }

        data = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.8,
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": "Ты пишешь вдохновляющие мотивационные цитаты на русском языке."},
                {"role": "user", "text": f"Напиши {prompt_text}."}
            ]
        }

        async with aiohttp.ClientSession() as session:
            print("📤 Данные запроса:", data)
            async with session.post(url, headers=headers, json=data) as resp:
                response = await resp.json()
                print("📥 Ответ от Yandex:", response)
                logging.info("Yandex GPT response:")
                logging.info(response)

                if "result" in response:
                    return response["result"]["alternatives"][0]["message"]["text"]
                elif "error" in response:
                    error_message = response["error"].get("message", "Неизвестная ошибка")
                    error_code = response["error"].get("code", "unknown_code")
                    logging.error(f"Yandex GPT API Error: {error_code} — {error_message}")
                    return f"⚠️ Ошибка от Yandex GPT: {error_message}"
                else:
                    logging.error("Непредвиденный ответ от Yandex GPT")
                    return "⚠️ Не удалось обработать ответ от Yandex GPT."
    except Exception as e:
        logging.exception("Исключение при запросе к Yandex GPT")
        return "⚠️ Произошла ошибка при подключении к Yandex GPT."