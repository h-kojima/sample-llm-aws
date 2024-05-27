import streamlit as st
import boto3
import json

st.title("Bedrock Chat Application using Claude 3 model on ROSA HCP")

# Bedrock Runtimeサービス用のクライアント
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-west-2')
    
def format_chat_history(messages):
    formatted_history = ""
    for message in messages:
        # ユーザーかアシスタントかに応じてロールを設定
        role = "Human:" if message["role"] == "user" else "Assistant:"
        # メッセージを整形して追加
        formatted_history += f"{role} {message['content']}\n"
    return formatted_history

# チャット履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# アプリ再実行時にチャットメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力の受け取り
if prompt := st.chat_input("このテキストボックスに文章を入力して下さい"):
    # ユーザーメッセージをチャットメッセージコンテナに表示
    with st.chat_message("user"):
        st.markdown(prompt)
    # ユーザーメッセージをチャット履歴に追加
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 対話履歴を整形してモデルの入力用に準備
    chat_history = format_chat_history(st.session_state.messages)

    # アシスタントの応答をチャットメッセージコンテナに表示
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 整形された対話履歴と新しいユーザー入力をモデルに送信
        body = json.dumps({
            'max_tokens': 4000,
            "messages": [{"role": "user", "content": prompt}],
            "anthropic_version": "bedrock-2023-05-31"
        })
        accept = 'application/json'
        contentType = 'application/json'
        model_id = 'anthropic.claude-3-haiku-20240307-v1:0'
        #model_id = 'anthropic.claude-3-opus-20240229-v1:0'
        #model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

        response = bedrock.invoke_model_with_response_stream(
            body=body, modelId=model_id, accept=accept, contentType=contentType)
        stream = response.get('body')

        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                # 取得したチャンクを追加し、Streamlitに表示
                chunk_json = json.loads(chunk.get("bytes").decode())
                if chunk_json["type"]=="content_block_delta":
                    full_response += str(chunk_json["delta"]["text"])
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        # アシスタントの応答をチャット履歴に追加
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
