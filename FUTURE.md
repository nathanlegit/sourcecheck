## Fetch performance and optimisation for fetch_eu.py 22 August 2026

scripts/fetch_eu.py fetch 113 seperate pages and currently opens a new TCP connection and TLS handshake via a fresh request.get() call. Increases runtime by a substancial amount. 

Fix: to use request.session() to persist a single connection across all requests to the same host via connnection polling/keep alive. Applu when script needs to run again from scratch and for further improvement. 