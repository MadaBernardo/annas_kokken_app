#imagem base do python
FROM python:3.11-slim

#definir diretorio de trabalho
WORKDIR /app

#copiar files de dependencias
COPY requirements.txt .

#instalr dependencias sem guardar caches
RUN pip install --no-cache-dir -r requirements.txt

#copiar o resto do codigo do frontend
COPY . .

#expor a porta padrão
EXPOSE 8501

#iniciar o streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]