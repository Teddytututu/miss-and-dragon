# Optional voice reading

Voice reading stays an optional local add-on. Miss & Dragon ships links and preference handling only; model weights and voice files remain outside this repository.

| Project | License | Commercial use | Voice source | Recommendation |
| --- | --- | --- | --- | --- |
| [CosyVoice code](https://github.com/FunAudioLLM/CosyVoice) | Apache-2.0 | Follow the Apache-2.0 notice, attribution and redistribution terms, plus each model card and dependency notice | Official project voices and user-provided local voices | Recommended as the documented integration path |
| FeiyuVoice-CosyVoice3 model | Upstream CosyVoice components use Apache-2.0; the model package has no repository-wide license for local contributions and character assets | Review every upstream component and asset term before commercial distribution | Model card records authorization from the real voice owner | Not recommended: voice taken from a real person; not linked |

The first-run assistant asks about voice reading only when it sees an NVIDIA GPU with at least 6 GiB of reported memory and at least 10 GiB free on the project disk. Unsupported machines keep voice reading disabled and skip the question. A qualifying machine can record the choice with `--enable-voice` or `--disable-voice`.

Installation follows the official [CosyVoice installation guide](https://github.com/FunAudioLLM/CosyVoice#installation). Users supply the model and voice assets under the terms that accompany those assets.
