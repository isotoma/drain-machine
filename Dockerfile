FROM python:3.7
RUN mkdir /app
WORKDIR /app
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x /app/kubectl
RUN pip install pipenv
COPY Pipfile /app
COPY Pipfile.lock /app
RUN pipenv install
COPY docker-entrypoint.py /app
COPY drainmachine /app/drainmachine
ENTRYPOINT ["pipenv", "run", "/app/docker-entrypoint.py"]