# gpt-slack-matome

This script generates weekly Slack summary from conversation history of a channel.
The style is like casual news sites.

```sh
$ python main.py https://hello-ai.slack.com/archives/CABCDE/p123456789

ウィークリー #random まとめ (2023-03-06 ~ 2023-03-13):
・メガネで花粉症対策をしたAさん、オフィスに着くも誰もいなくてクスッと笑う [link](https://hello-ai.slack.com/archives/CABCDE/p123456)
・DeNAの後輩からAR体験をもらったBさん、店舗やユーザーに最高の体験を提供したいと改めて思う [link](https://hello-ai.slack.com/archives/CABCDE/p123456)
・「エアビーの部屋借りてアロマを作る会」で、実はアロマ作りが初めてだったCさんが、ローズマリーのアロマを作って、自分でも似合わなすぎると困惑 [link](https://hello-ai.slack.com/archives/CABCDE/p123456)
```

URL is the link to the latest message in the channel

You need  `SLACK_USER_TOKEN` and `OPENAI_API_KEY` as environment variables
