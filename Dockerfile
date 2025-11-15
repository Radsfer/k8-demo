# Usar uma imagem base leve do Python
FROM python:3.10-slim

# Instalar o Flask
RUN pip install Flask

# Definir o diretório de trabalho
WORKDIR /app

# Copiar nossa aplicação
COPY app.py .

# Definir a variável de ambiente para o Flask
ENV FLASK_APP=app.py

# Expor a porta que o Flask usará
EXPOSE 5000

# Comando para iniciar o servidor
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
