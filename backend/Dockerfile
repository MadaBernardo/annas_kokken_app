# 1. Escolher a imagem base com Python
FROM python:3.11-slim

# 2. Definir a pasta de trabalho dentro do contentor
WORKDIR /app

# 3. Copiar o ficheiro de dependências
COPY requirements.txt .

# 4. Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo o código do projeto para o contentor
COPY . .

# 6. Definir o comando que arranca a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]