# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    tk \ 
    && rm -rf /var/lib/apt/lists/*
    

RUN git clone https://github.com/janeswh/ca_imaging_analysis.git .

RUN pip3 install -r requirements.txt
RUN python -m pip install openpyxl


EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "ROI_analysis_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
