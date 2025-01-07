from typing import Any, Mapping
from google.cloud.discoveryengine_v1alpha import SearchServiceClient, SearchRequest
from google.protobuf.json_format import MessageToDict
#from oauth2client import client
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
import functions_framework, flask, os

PROJECT_ID="gen-lang-client-0423982855"
PROJECT_NUMBER="955675926935"
GOOGLE_API_KEY="AIzaSyCDS48ssorXl7InG0Dg38ZH_QFdvHTFiqs"# Google Chatから送られてくるBearer Tokenの整合に使用
CHAT_ISSUER="https://accounts.google.com"
PUBLIC_CERT_URL_PREFIX="https://www.googleapis.com/service_accounts/v1/metadata/x509/955675926935-compute@developer.gserviceaccount.com"
 
# Gemini モデルとのチャットを行う関数
def gemini_chat(message, history, temperature, top_p, top_k, max_output_token):
  
    # Gemini モデルの初期化
    generation_config = {
        "temperature": temperature,  # 生成するテキストのランダム性を制御
        "top_p": top_p,          # 生成に使用するトークンの累積確率を制御
        "top_k": top_k,          # 生成に使用するトップkトークンを制御
        "max_output_tokens": max_output_token,  # 最大出力トークン数を指定
    }
    
    gemini_model = GenerativeModel(
        model_name="gemini-1.0-pro",
        generation_config=generation_config
    )
    
    # 会話履歴のリストを初期化
    gemini_history = []
    
    # 会話履歴のフォーマットを整形
    for row in history:
        input_from_user = row[0]
        output_from_gemini = row[1]
    
        gemini_history.append(Content(role="user", parts=[Part.from_text(input_from_user)]))
        gemini_history.append(Content(role="model", parts=[Part.from_text(output_from_gemini)]))
    
    # Gemini モデルに会話履歴をインプット
    chat = gemini_model.start_chat(history=gemini_history)
    
    # Gemini モデルにプロンプトリクエストを送信
    try:
        response = chat.send_message(message).text
  
    except IndexError as e:
        print(f"IndexError: {e}")
        return "Gemini からレスポンスが返されませんでした。もう一度質問を送信するか、文章を変えてみてください。"
    
    return response

# チャットボットが実際に出力するメッセージを作成する
def create_message(text: str) -> Mapping[str, Any]:
    result = gemini_chat(text=text)
    
    # 返信文作成
    cards = {
        "cardsV2": [
            {
                "cardId": "searchResults",
                "card": {
                    "sections": [
                        {
                            "collapsible": False,
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": "<b>回答文</b><br>" + result["summary"]
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
  
# チャットボットからメッセージを受信 → create_message() で作成した JSON を返す
@functions_framework.http
def get_chat(req: flask.Request):
    if req.method == "GET":
        return flask.make_response(flask.jsonify({"message": "Method Not Allowed"}), 405)
    try:
        token = client.verify_id_token(bearer_token, PROJECT_NUMBER, cert_uri=PUBLIC_CERT_URL_PREFIX + CHAT_ISSUER)
        if token['iss'] != CHAT_ISSUER:
            return flask.make_response(flask.jsonify({"message": "Unauthorized"}), 401)
    except Exception as e:
        return flask.make_response(flask.jsonify({"message": "Unauthorized", "error": str(e)}), 401)
    
    request_json = req.get_json(silent=True)
    if not request_json or 'message' not in request_json or 'text' not in request_json['message']:
        return flask.make_response(flask.jsonify({"message": "Bad Request"}), 400)
    
    text = request_json["message"]["text"]
    response = create_message(text=text)
    return response

