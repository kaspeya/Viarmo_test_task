FROM python:3.8.18-slim-bullseye

RUN apt-get update \
    && apt-get install -y wget \
    && apt-get install -y unzip gnupg2 xvfb libxi6 libgconf-2-4 libnss3-dev\
    && wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip -O /opt/chromedriver_linux64.zip \
    && unzip /opt/chromedriver_linux64.zip -d /opt/ \
    && ln -s /opt/chromedriver_linux64/chromedriver /usr/bin/ \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm /opt/chromedriver_linux64.zip \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /root/.cache/*

COPY requirements.txt /tmp/

RUN cat /tmp/requirements.txt | xargs --no-run-if-empty -n 1 pip install \
    && rm -rf /tmp/* /root/.cache/*

COPY updater_tool /app/
WORKDIR /app
CMD ['python', 'process.py']
