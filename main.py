# REQUIRE: SLACK_USER_TOKEN, OPENAI_API_KEY

import datetime
import os
import sys
import requests
import re
import openai

user_data = {}
token = os.environ['SLACK_USER_TOKEN']

def get_user_info(user_id):
  if user_id in user_data:
    return user_data[user_id]

  slack_url = 'https://slack.com/api/users.info'

  headers = {
    'Authorization': f'Bearer {token}',
    'Content-type': 'application/json; charset=utf-8'
  }

  params = {
    'user': user_id
  }

  response = requests.get(slack_url, params=params, headers=headers)
  data = response.json()

  if data['ok']:
    user_data[user_id] = data['user']
    return data['user']
  else:
    error = data['error']
    print(f"Error fetching username for user ID {user_id}: {error}")

def fetch_channel_history(channel_id, oldest=None, latest=None):
  slack_url = 'https://slack.com/api/conversations.history'
  inclusive = True # include the thread's original message in the response

  headers = {
    'Authorization': f'Bearer {token}',
    'Content-type': 'application/json; charset=utf-8'
  }

  messages = []
  cursor = None

  while True:
    params = {
      'channel': channel_id,
      'inclusive': inclusive,
      'cursor': cursor,
      'latest': latest,
      'oldest': oldest,
    }

    response = requests.get(slack_url, params=params, headers=headers)

    data = response.json()
    if 'messages' in data and len(data['messages']) > 0:
      messages = messages + data['messages']
      if float(data['messages'][0]['ts']) < oldest:
        break
    else:
      break

    if data['has_more'] == False:
      break

    cursor = data['response_metadata']['next_cursor']

  messages.reverse()
  content = ''
  for message in messages:
    if 'user' not in message:
      continue
    if 'bot_id' in message:
      continue

    user_info = get_user_info(message['user'])
    ts = message['ts']
    time_str = datetime.datetime.fromtimestamp(float(ts)).strftime('%m-%d %H:%M')

    if 'subtype' in message and (message['subtype'] == 'channel_leave' or message['subtype'] == 'channel_join'):
      continue
    text = message['text']

    content += f"{time_str} [{ts}]\n{user_info.get('real_name')}:\n{text}\n"
    if 'attachments' in message:
      for attachment in message['attachments']:
        if 'text' in attachment:
          content += "```\n" + attachment['text'] + "\n```"

    content += "\n"

  return content

def get_channel_name(channel_id):
  url = "https://slack.com/api/conversations.info"

  # Define the request parameters, including the Slack bot token and channel ID
  params = {
      "token": os.environ["SLACK_USER_TOKEN"],
      "channel": channel_id
  }

  response = requests.get(url, params=params)
  json_response = response.json()

  channel_name = json_response["channel"]["name"]
  return channel_name

def generate_summary(now, host):
  beginning_of_week = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
  oldest_ts = (beginning_of_week - datetime.timedelta(days=7)).timestamp()
  latest_ts = beginning_of_week.timestamp()

  begin_str = (beginning_of_week - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
  end_str = beginning_of_week.strftime('%Y-%m-%d')

  content = fetch_channel_history(channel_id, oldest=oldest_ts, latest=latest_ts)

  input_content = ""
  # loop through lines of content
  max_length = 1024 * 2
  for line in content.splitlines():
    if len(line) > max_length:
      break
    max_length -= len(line)

    input_content += line + "\n"

  if 'DEBUG' in os.environ:
    print(input_content)
    print("\n---\n\n")

  prompt = """
  Slackのログが与えられます
  まとめニュースを面白おかしく箇条書きで3行で生成します
  行末に参照した timestamp を付けてください

  例:
  ・Hiroshi Yamamoto さんがアロマ作りに挑戦し、困惑した様子を報告  [1678521686.362439]
  ・Tomomi Ishihara さんが花粉症対策でメガネを買ったことが話題に [1678521686.362439]
  """

  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
          {"role": "system", "content": prompt},
          {"role": "user", "content": input_content},
      ]
  )

  answer = response['choices'][0]['message']['content']

  answer = re.sub(r'\[(\d+)\.(\d+)\]', rf'[link]({host}/archives/{channel_id}/p\1\2)', answer)

  print(f"ウィークリー #{channel_name} まとめ ({begin_str} ~ {end_str}):\n" + answer)

if __name__ == '__main__':
  url = sys.argv[1]
  match = re.search(r'^(.+)/archives/(\w+)/p(\d+)$', url)

  if not match:
    print('Invalid URL')
    sys.exit()

  host = match.group(1)
  channel_id = match.group(2)
  thread_ts = match.group(3)

  channel_name = get_channel_name(channel_id)

  for i in range(10):
    now = datetime.datetime.now() - datetime.timedelta(days=i * 7)
    generate_summary(now, host)
    print("\n")
