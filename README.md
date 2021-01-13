# dialog-de

[![Documentation Status](https://readthedocs.org/projects/dialog-de/badge/?version=latest)](https://dialog-de.readthedocs.io/en/latest/)
[![Build Status](https://travis-ci.org/nikuya3/dialog-de.svg?branch=master)](https://travis-ci.org/nikuya3/dialog-de)

dialogue systems are still subject to open research and one might suspect that
deep learning architectures can lead to new SOTA in this field. The easiest approach would be to
use an unsupervised language model like BERT or GPT-3 as is. This approach is rather limited however, especially
for chatbots which are not general-purpose. A recent paper [0] has shown empirically that deep learning models
trained on dialogue data specifically perform better than BERT and GPT-2. Most of these dialogue-based deep learning models
are only available for the English language, however. Therefore, this project attempts to create a dialogue model suited
for the German language by assembling a German dialogue dataset.

## Goal
There are multiple approaches to chatbots. A common first step of a chatbot is to define __intents__ using a set of
utterances. If a user messages a chatbot, the chatbot attempts to detect the intent of the message and responds with a
corresponding hand-coded answer. The dataset for this intent detection has to be manually entered, thus there is
oftentimes only very little data available. Hence, intent detection is a few-shot learning task and finetuning on larger
unsupervised language models fails. 

This first chatbot step of __intent detection__ will serve as demo of this project. The goal is to train a model which
learns dialogue-specific text representations using a dialogue dataset. These representations can then be used for an
intent detection classifier. This classifier can then be evaluated with the F1-score metric similar to [0].

## Models
The ConveRT model [1] was proposed last year and holds the first place in the comparison of [0]. The model is pretrained
on English Reddit comments using a response selection task. However, the authors did not provide a reference
implementation and too little information to recreate it. Additionally, they found that ConveRT representations
miss certain language information and have to be complemented with a general purpose language representation [2].

Another approach is then to start with a pretrained language model (like BERT), train it on dialogue data and
use the resulting model for dialogue representations. This has been successfully attempted with the TOD-BERT model [3].
This model architecture will be used in this project. distil-bert-german [4] will be used as pretrained language model.

## Dataset
A Reddit conversation dataset consisting of German language only will be assembled. However, the dataset will be
structured in a way so that other sources could potentially be added (such as forums, QA sites, chats). The goal will
be to provide a dataset of similar quality and structure to the MetaLWOz dataset [5] used to train TOD-BERT. This
requires heavy manual heuristics in the data collection.

## Work breakdown
* Dataset creation: 20
* training the network: 10
* building an application (small chatbot): 10
* writing the final report: 3
* preparing the presentation of your work: 1

## Usage
Clone the repo using the `--recursive` flag or issue `git submodule update`. Then:

```
pip install -r requirements.txt
pip install -e .
cd ToD-BERT; git apply ../ToD-BERT.patch; cd .. 
./get_data.sh
./train_model.sh
```

Alternatively, the provided `Dockerfile` can be used to skip the first two steps. For this, both [Docker](https://docs.docker.com/get-docker/) and [nvidia-docker](https://github.com/NVIDIA/nvidia-docker) have to be installed. The image built with the below command will include [apex](https://github.com/NVIDIA/apex) for automatic mixed precision and [faiss](https://github.com/facebookresearch/faiss) for negative sampling based on k-means.

```
nvidia-docker build -t dialog-de .
nvidia-docker run -v `pwd`:/workspace:rw -it dialog-de bash
./train_model --amp --kmeans
```

The resulting model will be stored in `save/pretrain/ToD-BERT-German-JNT`. The latest checkpoint can should be used for the chatbot demo. In order to do this, find the latest checkpoint (e.g. using `ls save/pretrain/ToD-BERT-German-JNT`) and (optionally) convert it into a tensorflow checkpoint:

```
./convert_model.py save/pretrain/ToD-BERT-German-JNT/[INSERT_CHECKPOINT_DIR]
```

Finally, the checkpoint directory needs to specified in the `demo/config.yml` file (replace all occurences of `[INSERT_CHECKPOINT_DIR]`). Then, the demo can be trained using `./train_demo.sh` and run using `./run_demo.sh`. The models can also be evaluated using `./evaluate_demo.sh`.

The chatbot data was adapted from: https://github.com/zdi-mainfranken/corona-chatbot.

[0]: https://arxiv.org/abs/2010.13912
[1]: https://arxiv.org/abs/1911.03688
[2]: https://arxiv.org/abs/2003.04807
[3]: https://arxiv.org/abs/2004.06871
[4]: https://huggingface.co/distilbert-base-german-cased
[5]: https://www.microsoft.com/en-us/research/project/metalwoz/
