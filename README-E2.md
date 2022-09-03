# Ejercicio 2

Se cambió la configuración de creación de imágen del cliente para que no copie el archivo de configuración:
```diff
[client/Dockerfile]
< COPY ./client/config.yaml /config.yaml
```

Se agregaron los campos para montar como volúmenes los archivos de configuración en el cliente y el servidor:
```diff
[docker-compose-dev.yaml]
> volumes:
>   - ./client/config.yaml:/config.yaml:ro
...
> volumes:
>   - ./server/config.ini:/config.ini:ro
```
