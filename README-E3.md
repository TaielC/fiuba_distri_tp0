# Ejercicio 3

Se puede utilizar `scripts/test_with_netcat.sh` para ejecutar una prueba del servidor.
El mismo crea (y remueve al finalizar) un contenedor de docker utilizando la imágen `bash` y agregandose a la red definida en el docker-compose.

Ejemplo:
```bash
$ scripts/test_with_netcat.sh
Enter input to send to server: Hello
Sending: Hello
Your Message has been received: Hello
Enter input to send to server: panes
Sending: panes
Your Message has been received: panes
Enter input to send to server: Exiting...
```
