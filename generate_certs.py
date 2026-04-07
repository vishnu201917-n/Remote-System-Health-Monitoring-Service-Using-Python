#!/usr/bin/env python3

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


CERT_DIR = "certs"
os.makedirs(CERT_DIR, exist_ok=True)


def generate_key():
    """2048-bit RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def save_key(key, path):
    """Save private key to file."""
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    print(f"  saved: {path}")


def save_cert(cert, path):
    """Save certificate to file."""
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"  saved: {path}")


def make_ca():
    """Generate self-signed CA certificate."""
    key  = generate_key()
    name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,            "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,  "Karnataka"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,       "MonitoringCA"),
        x509.NameAttribute(NameOID.COMMON_NAME,             "MonitoringRootCA"),
    ])
    now  = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)                          # self-signed
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    return key, cert


def make_signed_cert(common_name, ca_key, ca_cert, is_server=False):
    """Generate a certificate signed by the CA."""
    key  = generate_key()
    name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,            "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,  "Karnataka"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,       "Monitoring"),
        x509.NameAttribute(NameOID.COMMON_NAME,             common_name),
    ])
    now  = datetime.datetime.now(datetime.timezone.utc)

    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)               # signed by CA
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )

    
    if is_server:
        import ipaddress
        builder = builder.add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address("10.1.0.91")),  
        ]),
        critical=False
        )
    cert = builder.sign(ca_key, hashes.SHA256())    # CA signs it
    return key, cert


def main():
    print("\n[*] Generating SSL certificates ...\n")

    print("[1] Certificate Authority")
    ca_key, ca_cert = make_ca()
    save_key(ca_key,  f"{CERT_DIR}/ca.key")
    save_cert(ca_cert, f"{CERT_DIR}/ca.crt")

    print("\n[2] Server certificate")
    srv_key, srv_cert = make_signed_cert("localhost", ca_key, ca_cert, is_server=True)
    save_key(srv_key,   f"{CERT_DIR}/server.key")
    save_cert(srv_cert, f"{CERT_DIR}/server.crt")

    print("\n[3] Client certificate")
    cli_key, cli_cert = make_signed_cert("agent", ca_key, ca_cert)
    save_key(cli_key,   f"{CERT_DIR}/client.key")
    save_cert(cli_cert, f"{CERT_DIR}/client.crt")

    print("\n[+] All certificates saved to ./certs/")


if __name__ == "__main__":
    main()
