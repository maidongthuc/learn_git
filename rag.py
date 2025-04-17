"""
This example is about how to use the streaming interface to start a chat request
and handle chat events
"""

import os
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_COM_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'pat_KyZngnD9AeJ3UOcWI3cZ8ZtAWYNckOAsr9QeU1tadp8N3ivY6pEwW2pocuQ2UlAT'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_COM_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType, ChatEventType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = '7490748196700995592'
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = 'user_id_17'

for event in coze.chat.stream(
    bot_id=bot_id,
    user_id=user_id,
    auto_save_history=True,
    additional_messages=[
        Message.build_user_question_text("xin chào, bạn là ai?"),
    ],
):
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="", flush=True)

    if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
        print()

while True:
    user_input = input("Nhập câu hỏi của bạn (hoặc gõ 'exit' để thoát): ")
    if user_input.lower() == "exit":
        print("Thoát chương trình.")
        break

    for event in coze.chat.stream(
        bot_id=bot_id,
        user_id=user_id,
        chat_history_id=None,
        auto_save_history=True,
        additional_messages=[
            Message.build_user_question_text(user_input),
        ],
    ):
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            print(event.message.content, end="", flush=True)

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            print()
