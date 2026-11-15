# Contributing to OlhoVivo

Rules: no emoji anywhere (code, docs, commits). No AI co-author trailers in commits. Run git config core.hooksPath .githooks after cloning.

Work on develop. Tests must pass offline (pytest), ruff clean, and python scripts/check_no_emoji.py clean. Tests must not touch the network or download models.

Never commit real data: no real licence plates, images or video. Use synthetic plates in the FAKE0NN pattern, which is not a valid Brazilian plate format.

OlhoVivo is decision support. Do not add code that issues a fine or takes any enforcement action without a human confirming it.
