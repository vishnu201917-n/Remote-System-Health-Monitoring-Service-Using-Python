#!/usr/bin/env python3

import argparse, json, logging, socket, ssl, time
import psutil

logging.basicConfig(format='%(asctime)s [AGENT] %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
log = logging.getLogger()

parser = argparse.ArgumentParser()
parser.add_argument('--name',     default=socket.gethostname() + '-' + str(__import__('random').randint(1,999)), help='Agent name')
parser.add_argument('--server',   default='127.0.0.1',          help='Server IP')
parser.add_argument('--interval', default=5, type=int,          help='Seconds between reports')
args = parser.parse_args()

SERVER   = args.server
UDP_PORT = 9000
TLS_PORT = 9001
INTERVAL = args.interval
CERT_DIR = 'certs'
NODE_ID  = args.name

THRESHOLDS = {'cpu_percent': 85.0, 'mem_percent': 90.0, 'disk_percent': 90.0}


# Metric collection 

def collect_metrics():
    return {
        'cpu_percent':    round(psutil.cpu_percent(interval=1), 2),
        'mem_percent':    round(psutil.virtual_memory().percent, 2),
        'disk_percent':   round(psutil.disk_usage('/').percent, 2),
        'net_bytes_sent': psutil.net_io_counters().bytes_sent,
        'net_bytes_recv': psutil.net_io_counters().bytes_recv,
        'process_count':  len(psutil.pids()),
    }


# UDP sender 

def send_metrics_udp(udp_sock, metrics):
    msg = json.dumps({
        'type':     'metrics',
        'hostname': NODE_ID,
        'metrics':  metrics,
    }).encode()
    udp_sock.sendto(msg, (SERVER, UDP_PORT))


# TLS connection 


def tls_connect():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(f'{CERT_DIR}/ca.crt')
    ctx.load_cert_chain(f'{CERT_DIR}/client.crt', f'{CERT_DIR}/client.key')

    raw  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = ctx.wrap_socket(raw, server_hostname=SERVER)
    conn.connect((SERVER, TLS_PORT))
    log.info(f"TLS connected  cipher={conn.cipher()[0]}  version={conn.version()}")

    conn.sendall((json.dumps({
        'type':     'register',
        'hostname': NODE_ID,
        'platform': 'Linux',
    }) + '\n').encode())

    return conn


def send_alert_tls(tls_conn, metric, value):
    tls_conn.sendall((json.dumps({
        'type':     'alert',
        'hostname': NODE_ID,
        'metric':   metric,
        'value':    value,
    }) + '\n').encode())

def listen_for_server_alerts(conn):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            for line in data.split(b'\n'):
                if line:
                    msg = json.loads(line.decode())

                    if msg.get('type') == 'server_alert':
                        print(f"[SERVER ALERT] {msg['metric']} = {msg['value']}")

        except:
            break


#main 

def main():
    log.info(f"Agent '{NODE_ID}' starting")
    log.info(f"UDP  metrics → {SERVER}:{UDP_PORT}")
    log.info(f"TLS  alerts  → {SERVER}:{TLS_PORT}")

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    tls_conn = None

    while True:
        try:
            if tls_conn is None:
                tls_conn = tls_connect()
                import threading
                threading.Thread(target=listen_for_server_alerts, args=(tls_conn,), daemon=True).start()

            metrics = collect_metrics()

            send_metrics_udp(udp_sock, metrics)
            log.info(f"UDP sent  CPU={metrics['cpu_percent']}%  "
                     f"MEM={metrics['mem_percent']}%  "
                     f"DISK={metrics['disk_percent']}%")

            for metric, limit in THRESHOLDS.items():
                if metrics.get(metric, 0) >= limit:
                    send_alert_tls(tls_conn, metric, metrics[metric])
                    log.warning(f"TLS alert sent  {metric}={metrics[metric]}")

        except Exception as e:
            log.error(f"Error: {e} — reconnecting TLS in 5s")
            try: tls_conn.close()
            except: pass
            tls_conn = None
            time.sleep(5)
            continue

        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
