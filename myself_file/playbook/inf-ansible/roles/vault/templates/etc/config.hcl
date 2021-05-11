ui = true

listener "tcp" {
  address = "{{ ansible_host }}:8200"
  cluster_address = "{{ ansible_host }}:8201"
  tls_cert_file = "{{ main_path }}/etc/certs/vault.service.upyun.crt"
  tls_key_file  = "{{ main_path }}/etc/certs/vault.service.upyun.key"
}

storage "consul" {
  address = "127.0.0.1:7500"
  path    = "vault/"
}
