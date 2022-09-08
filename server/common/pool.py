from multiprocessing import Pool


def with_pool(pool_size):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Pool(pool_size) as pool:
                return func(*args, pool=pool, **kwargs)

        return wrapper

    return decorator

