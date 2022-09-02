# Ejercicio 1

Simplemente ejecutar
```
make docker-compose-up
```

# Ejercicio 1.1

Se agregó un script que utiliza un template de jinja para la creación de la configuración de docker-compose con cantidad variable de clientes.
Para configurar los mismos se puede utilizar la variable de entorno `CLIENTS` (o con un archivo .env):

```
$ make docker-compose-up CLIENTS=5
```
ó
```
$ echo CLIENTS=5 > .env
$ make docker-compose-up
```
