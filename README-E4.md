# Ejercicio 4

Se agregó el manejo de `SIGTERM` (y `SIGINT`) para que tanto el cliente como el servidor puedan terminar su ejecución de forma ordenada.

## Cliente

```go
    // Setup signals
    sigs := make(chan os.Signal, 1)
    signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
// in loop:
    // ...
    case s := <-sigChan:
        log.Errorf(
            "[CLIENT %v] %v received. Exiting...",
            c.config.ID,
            s,
        )
        break loop
    // ...
```


## Servidor

```python
import signal


class TerminationSignal(Exception):
    pass


def _set_sigterm_handler():
    """
    Setup SIGTERM signal handler. Raises StopServer exception when SIGTERM
    signal is received
    """
    def signal_handler(_signum, _frame):
        logging.info("SIGTERM received")
        raise TerminationSignal()

    signal.signal(signal.SIGTERM, signal_handler)
```

