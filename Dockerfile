# # app/Dockerfile

# FROM python:3.9-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \  
#     curl \
#     software-properties-common \
#     git \
#     tk \ 
#     && rm -rf /var/lib/apt/lists/*
    
# # RUN git clone https://github.com/janeswh/ca_imaging_analysis.git .
# COPY requirements.txt ./
# COPY ROI_analysis_web.py ./

# RUN pip3 install --no-cache-dir -r requirements.txt
# RUN python -m pip install openpyxl

# EXPOSE 8501
  
# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
# ENTRYPOINT ["streamlit", "run", "ROI_analysis_web.py", "--server.port=8501", "--server.address=0.0.0.0"]




# app/Dockerfile

FROM python:3.11-slim AS build

# virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# add and install requirements
# RUN git clone https://github.com/janeswh/ca_imaging_analysis.git .

# RUN apt-get update && rm -rf /var/lib/apt/lists/*

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     curl \
#     software-properties-common \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip3 install -r requirements.txt \
    && python -m pip install openpyxl 

# # bypass email prompt
# RUN mkdir -p /root/.streamlit
# RUN bash -c 'echo -e "\
# [general]\n\
# email = \"\"\n\
# " > /root/.streamlit/credentials.toml'   

FROM python:3.11-slim AS runtime

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
    && rm -rf /var/lib/apt/lists/* 

# set working directory
WORKDIR /app_dir



# switch to non-root user
USER user

# Path
ENV PATH="/opt/venv/bin:$PATH"

# COPY ROI_Analysis_Home.py ./
# COPY pages/ ./
# COPY . .
COPY ./app .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "Home.py", "--server.fileWatcherType=none", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
# ENTRYPOINT ["streamlit", "run", "ROI_analysis_web.py", "--server.port=8501", "--server.headless=true"]

