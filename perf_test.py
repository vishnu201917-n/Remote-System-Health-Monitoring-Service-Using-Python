#!/usr/bin/env python3

import json, os, socket, ssl, threading, time, uuid

SERVER   = '127.0.0.1'
PORT     = 9001
CERT_DIR = 'certs'


def make_ctx():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(f'{CERT_DIR}/ca.crt')
    ctx.load_cert_chain(f'{CERT_DIR}/client.crt', f'{CERT_DIR}/client.key')
    return ctx


def make_msg():
    return (json.dumps({
        'type': 'metrics', 'hostname': 'perf-node',
        'metrics': {'cpu_percent': 50.0, 'mem_percent': 60.0, 'disk_percent': 40.0,
                    'net_bytes_sent': 0, 'net_bytes_recv': 0, 'process_count': 100}
    }) + '\n').encode()


# Test 1: Throughput
def test_throughput(n=200):
    print(f"\n--- TEST 1: Throughput ({n} messages, 1 client) ---")
    ctx  = make_ctx()
    raw  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = ctx.wrap_socket(raw, server_hostname=SERVER)
    conn.connect((SERVER, PORT))
    conn.sendall((json.dumps({'type':'register','hostname':'perf','platform':'test'})+'\n').encode())

    msg  = make_msg()
    t0   = time.perf_counter()
    for _ in range(n):
        conn.sendall(msg)
    elapsed = time.perf_counter() - t0
    conn.close()

    print(f"  Sent    : {n} messages")
    print(f"  Time    : {elapsed:.3f}s")
    print(f"  Rate    : {n/elapsed:.0f} msg/s")


# Test 2: Concurrent clients 
def test_concurrent(clients=10, msgs=50):
    print(f"\n--- TEST 2: Concurrent ({clients} clients x {msgs} msgs) ---")
    ctx     = make_ctx()
    results = []
    lock    = threading.Lock()
    barrier = threading.Barrier(clients + 1)

    def sender():
        raw  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = ctx.wrap_socket(raw, server_hostname=SERVER)
        conn.connect((SERVER, PORT))
        conn.sendall((json.dumps({'type':'register','hostname':f'perf-{id(conn)}','platform':'test'})+'\n').encode())
        msg = make_msg()
        barrier.wait()
        t0 = time.perf_counter()
        for _ in range(msgs):
            conn.sendall(msg)
        elapsed = time.perf_counter() - t0
        conn.close()
        with lock:
            results.append(elapsed)

    threads = [threading.Thread(target=sender) for _ in range(clients)]
    for t in threads: t.start()
    barrier.wait()
    for t in threads: t.join()

    total   = clients * msgs
    max_dur = max(results)
    print(f"  Clients : {clients}")
    print(f"  Total   : {total} messages")
    print(f"  Rate    : {total/max_dur:.0f} msg/s (aggregate)")


# Test 3: Scalability 
def test_scalability():
    print(f"\n--- TEST 3: Scalability Ramp ---")
    ctx = make_ctx()
    for n in [1, 5, 10, 20]:
        results = []
        lock    = threading.Lock()
        barrier = threading.Barrier(n + 1)

        def sender():
            raw  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn = ctx.wrap_socket(raw, server_hostname=SERVER)
            conn.connect((SERVER, PORT))
            conn.sendall((json.dumps({'type':'register','hostname':f'p{id(conn)}','platform':'t'})+'\n').encode())
            msg = make_msg()
            barrier.wait()
            t0 = time.perf_counter()
            for _ in range(30):
                conn.sendall(msg)
            with lock:
                results.append(time.perf_counter() - t0)
            conn.close()

        threads = [threading.Thread(target=sender) for _ in range(n)]
        for t in threads: t.start()
        barrier.wait()
        for t in threads: t.join()
        pps = (n * 30) / max(results)
        print(f"  {n:3d} clients → {pps:6.0f} msg/s")


if __name__ == '__main__':
    print("=" * 40)
    print("  PERFORMANCE EVALUATION")
    print("=" * 40)
    test_throughput()
    test_concurrent()
    test_scalability()
    print("\nDone.")
