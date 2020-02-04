FROM python:3.7

RUN mkdir bot
ADD . bot
WORKDIR bot
RUN pip install

CMD python main.py
