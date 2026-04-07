#!/usr/bin/env python3
# server.py - Health Monitoring Server


import json, logging, socket, ssl, threading, time

logging.basicConfig(format='%(asctime)s [SERVER] %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
log = logging.getLogger()

UDP_PORT  = 9000
TLS_PORT  = 9001
CERT_DIR  = 'certs'

THRESHOLDS = {'cpu_percent': 85.0, 'mem_percent': 90.0, 'disk_percent': 90.0}

nodes      = {}       
nodes_lock = threading.Lock()


# Alert checker 

def check_alerts(hostname, metrics):
    for metric, limit in THRESHOLDS.items():

        val = metrics.get(metric, 0)

        if val >= limit:
            log.warning(f"*** ALERT node={hostname} {metric}={val}")

            with nodes_lock:
                node = nodes.get(hostname)

            if node and 'conn' in node:
                try:
                    node['conn'].sendall((json.dumps({
                    'type': 'server_alert',
                    'metric': metric,
                    'value': val
                    }) + '\n').encode())
                except Exception as e:
                    log.error(f"Send failed: {e}")

# UDP Receiver Thread

def udp_receiver():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    log.info(f"UDP  socket listening on port {UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(4096)          
            msg        = json.loads(data.decode())

            if msg.get('type') == 'metrics':
                hostname = msg['hostname']
                metrics  = msg['metrics']

                with nodes_lock:
                    if hostname not in nodes:
                        nodes[hostname] = {}

                    nodes[hostname]['metrics'] = metrics
                    nodes[hostname]['time'] = time.time()
                    nodes[hostname]['addr'] = addr

                log.info(f"UDP  METRICS  {hostname:15s}  "
                         f"CPU={metrics['cpu_percent']:5.1f}%  "
                         f"MEM={metrics['mem_percent']:5.1f}%  "
                         f"DISK={metrics['disk_percent']:5.1f}%")

                check_alerts(hostname, metrics)

        except Exception as e:
            log.error(f"UDP error: {e}")


# TLS Client Handler Thread

def handle_tls_client(conn, addr):
    log.info(f"TLS  connected from {addr}  cipher={conn.cipher()[0]}")
    buf = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                msg = json.loads(line.decode())

                if msg['type'] == 'register':
                    with nodes_lock:

                        if msg['hostname'] not in nodes:
                            nodes[msg['hostname']] = {}
                        nodes[msg['hostname']]['conn'] = conn

                elif msg['type'] == 'alert':
                    log.warning(f"TLS  ALERT     node={msg['hostname']}  "
                                f"{msg['metric']}={msg['value']}")
                    conn.sendall((json.dumps({'type': 'ack'}) + '\n').encode())

    except Exception as e:
        log.error(f"TLS client error {addr}: {e}")
    finally:
        log.info(f"TLS  disconnected: {addr}")
        conn.close()


# TLS Server Thread

def tls_server():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(f'{CERT_DIR}/server.crt', f'{CERT_DIR}/server.key')
    ctx.load_verify_locations(f'{CERT_DIR}/ca.crt')

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', TLS_PORT))
    server_sock.listen(10)
    log.info(f"TLS  socket listening on port {TLS_PORT}")

    while True:
        raw_conn, addr = server_sock.accept()
        try:
            tls_conn = ctx.wrap_socket(raw_conn, server_side=True)
        except ssl.SSLError as e:
            log.warning(f"TLS handshake failed from {addr}: {e}")
            raw_conn.close()
            continue
        threading.Thread(target=handle_tls_client,
                         args=(tls_conn, addr), daemon=True).start()

#main

def main():
    log.info("---- Health Monitoring Server starting ----")
    log.info(f"UDP  metrics  → port {UDP_PORT}")
    log.info(f"TLS  control  → port {TLS_PORT}")

    threading.Thread(target=udp_receiver, daemon=True).start()

    tls_server()


if __name__ == '__main__':
    main()
