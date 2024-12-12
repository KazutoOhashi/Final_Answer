FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive 
ENV LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja LC_ALL=ja_JP.UTF-8
ENV MYSQL_ROOT_PASSWORD=mysql

COPY 2-2.py /var/lib/ex2/
COPY my.cnf /etc/mysql/conf.d/

WORKDIR /var/lib/ex2

EXPOSE 3306

RUN apt update && apt install -y locales && \
    locale-gen ja_JP.UTF-8 && \
    apt upgrade -y
RUN apt install -y python3.8 python3-pip mysql-server
RUN pip3 install pandas requests beautifulsoup4 sqlalchemy pymysql
RUN service mysql start && \
    mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH 'mysql_native_password' BY '${MYSQL_ROOT_PASSWORD}'; FLUSH PRIVILEGES;" && \
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "CREATE DATABASE ex2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

CMD ["bash"]