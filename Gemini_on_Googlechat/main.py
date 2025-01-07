from typing import Any, Mapping
import openai  # OpenAI APIを使うためにインポート
from openai import OpenAI
import functions_framework, flask, os
from google.oauth2 import id_token
from google.auth.transport import requests

openai.api_key = ""

PROJECT_ID = "gen-lang-client-0423982855"
PROJECT_NUMBER = "955675926935"
CHAT_ISSUER = "https://accounts.google.com"
PUBLIC_CERT_URL_PREFIX = "https://www.googleapis.com/service_accounts/v1/metadata/x509/955675926935-compute@developer.gserviceaccount.com"

def gpt_chat(message: str) -> str:
    """
    OpenAI GPTモデルを使用してユーザーからの入力メッセージに応答を生成する。
    """
    try:
        completion = client.chat.completion.create(
            model="gpt-4",  # 必要に応じて "gpt-3.5-turbo" に変更可能
            messages=[
                {"role": "system", "content": "あなたは有能なアシスタントです。"},
                {"role": "user", "content": message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

def create_message(user_text: str) -> Mapping[str, Any]:
    """
    チャットボットが実際に出力するメッセージ(JSON)を作成する。
    gpt_chat() で取得した回答テキストを Google Chat のカード形式に整形して返す。
    """
    # GPT への問い合わせ
    gpt_response = gpt_chat(message=user_text)

    # Google Chat にカードで返すサンプル（cardsV2 を利用）
    cards = {
        "cardsV2": [
            {
                "cardId": "gptResultCard",
                "card": {
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        # GPTの出力をそのまま表示
                                        "text": gpt_response
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return cards


@functions_framework.http
def get_chat(req: flask.Request):
    """
    Google Chat のチャットボットに登録してあるエンドポイント。
    Google Chat からの POST リクエストを受け取り、テキストを解析し、
    GPT の結果を JSON (カードフォーマット) で返す。
    """
    # POST リクエスト以外は 405 で返す
    if req.method != "POST":
        return flask.make_response(flask.jsonify({"message": "Method Not Allowed"}), 405)

    # リクエストボディ(JSON)を取得
    request_json = req.get_json(silent=True)
    if not request_json:
        return flask.make_response(flask.jsonify({"message": "Bad Request"}), 400)

    # Google Chat では message.text にユーザーの入力が入る想定
    if "message" not in request_json or "text" not in request_json["message"]:
        return flask.make_response(flask.jsonify({"message": "Bad Request"}), 400)

    user_text = request_json["message"]["text"]

    # GPT からの回答を含むレスポンス JSON を作成
    response_cards = create_message(user_text)
    return flask.make_response(flask.jsonify(response_cards), 200)