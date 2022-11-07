FROM python:3.10-slim-bullseye

COPY ./requirements.txt /rl/requirements.txt

WORKDIR /rl

RUN apt -y update
RUN apt -y install htop
RUN pip install --disable-pip-version-check --root-user-action=ignore -r requirements.txt

COPY . /rl

ENTRYPOINT [ "python" ]
CMD [ "run.py" ]
