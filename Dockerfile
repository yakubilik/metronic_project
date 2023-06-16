FROM python:3.8-slim-buster

EXPOSE 5005

ADD main.py ./t-shirt_app/

ADD pdf_merger.py ./t-shirt_app/

ADD requirements.txt ./t-shirt_app/

ADD metronic_v8.0.37 ./t-shirt_app/metronic_v8.0.37/

ADD Orders-Ups ./t-shirt_app/Orders-Ups/

ADD merged_files ./t-shirt_app/merged_files/

ADD build.sh ./t-shirt_app/

RUN sh ./t-shirt_app/build.sh

WORKDIR /t-shirt_app

ADD main.py ./t-shirt_app/

CMD ["python3","./main.py"]