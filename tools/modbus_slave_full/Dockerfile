FROM python:3.11-slim

# 安装 Poetry
RUN pip install --no-cache-dir poetry==1.7.0

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装依赖（不包括开发依赖）
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 复制项目代码
COPY modbus_slave_full ./modbus_slave_full
COPY config.example.yaml ./config.yaml

# 暴露端口
EXPOSE 5020 8080

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行服务器
CMD ["python", "-m", "modbus_slave_full", "--config", "config.yaml"]
