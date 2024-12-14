FROM python:3.11
WORKDIR /
COPY . /
RUN pip install --upgrade pip
RUN python -m pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run","Home.py"]
