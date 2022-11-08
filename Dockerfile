FROM python:3.10-slim-bullseye

COPY ./requirements.txt /rl/requirements.txt

WORKDIR /rl

RUN pip install --disable-pip-version-check --root-user-action=ignore -r requirements.txt

COPY . /rl

ENTRYPOINT [ "python" ]
CMD [ "run.py" ]
