# Ejercicio 2

Se agregaron los campos para montar como volúmenes los archivos de configuración en el cliente y el servidor:
```diff
[docker-compose-dev.yaml]
> volumes:
>   - ./client/config.yaml:/config.yaml:ro
...
> volumes:
>   - ./server/config.ini:/config.ini:ro
```
