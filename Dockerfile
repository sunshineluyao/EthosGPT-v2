FROM python:3.12-slim
WORKDIR /project
RUN apt-get update && apt-get install -y --no-install-recommends \
    latexmk make poppler-utils texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
ENV PYTHONPATH=/project/src
CMD ["make", "reproduce-offline"]
