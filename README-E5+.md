# Ejercicios 5+

- Se implementó un protocolo que permite enviar dos tipos de requests al servidor: carga de datos (load) y consulta de datos (query).
    - Durante la carga de datos, el cliente envía batches de tamaño configurable al servidor, que en cada una almacena la información en un (archivo compartido)[#archivo-compartido].

    ```

- Para evitar los fenómenos de short-read y short-write, se implementaron iteraciones sobre las lecturas (o escrituras -en `python` existe `socket.sendall`-) de los sockets.

## Protocolo


Tipos de request:
```
| is_load          | client/agency |
| uint8/byte (0/1) | uint64        |
```

Batch de carga de datos:
```
| batch_len    | cupon_1 | cupon_2 | ... | cupon_n |
| uint64 (big) | ser_cu1 | ser_cu2 | ... | ser_cun |
```
Donde cada cupon (la agencia está dada por el cliente conectado):
```
| agency | first_name | last_name | id (DNI) | birth_date | number |
| string | string     | string    | uint64   | string     | uint64 |
```


## Archivo compartido

Para la sincronización con muchos procesos en el servidor al momento de lecturas o escrituras del archivo de storage, se utilizó un file-lock. Ver [implementacion](server/common/storage.py).
