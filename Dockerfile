# FROM python:3.11-slim AS build
FROM --platform=$BUILDPLATFORM python:3.11-slim AS build
# ARG TARGETPLATFORM

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt ./
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    gcc \
    && pip3 install -r requirements.txt \
    && python -m pip install openpyxl \
    && apt-get remove -y --purge make gcc build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* 

# RUN pip3 install -r requirements.txt \
#     && python -m pip install openpyxl 

ARG TARGETPLATFORM

FROM python:3.11 AS runtime

# setup user and group ids
ARG USER_ID=1000
ENV USER_ID $USER_ID
ARG GROUP_ID=1000
ENV GROUP_ID $GROUP_ID

# add non-root user and give permissions to workdir
RUN groupadd --gid $GROUP_ID user && \
          adduser user --ingroup user --gecos '' --disabled-password --uid $USER_ID && \
          mkdir -p /usr/src/app_dir && \
          chown -R user:user /usr/src/app_dir

# copy from build image
COPY --chown=user:user --from=build /opt/venv /opt/venv

RUN apt-get update && apt-get install --no-install-recommends -y tk \


# set working directory
WORKDIR /app_dir

# switch to non-root user
USER user

# Path
ENV PATH="/opt/venv/bin:$PATH"

COPY ./app .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "Home.py", "--server.fileWatcherType=none", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

