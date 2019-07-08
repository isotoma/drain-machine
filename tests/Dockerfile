FROM python:3
RUN mkdir /app
WORKDIR /app
RUN pip install Flask
COPY test_server.py /app
ENV FLASK_APP /app/test_server.py
CMD flask run --host=0.0.0.0
