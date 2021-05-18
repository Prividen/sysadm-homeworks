# Домашняя работа по занятию "3.9. Элементы безопасности информационных систем"

> 1. Установите [Hashicorp Vault](https://learn.hashicorp.com/vault) в виртуальной машине Vagrant/VirtualBox...
> 2. Запустить Vault-сервер в dev-режиме (дополнив ключ `-dev` упомянутым выше `-dev-listen-address`, если хотите увидеть UI)...

В -dev режиме vault хранит всё в памяти, было бы обидно потерять PKI при рестарте виртуалки. Я его "в продекшен" задеплоил, заодно поигрался со всякими unseal. 

--- 
> 3. Используя [PKI Secrets Engine](https://www.vaultproject.io/docs/secrets/pki), создайте Root CA и Intermediate CA.

Как-то так:
```hcl
# pki_admin.policy
# Enable secrets engine
path "sys/mounts/*" {
  capabilities = [ "create", "read", "update", "delete", "list" ]
}

# List enabled secrets engine
path "sys/mounts" {
  capabilities = [ "read", "list" ]
}

# Work with pki secrets engine
path "pki*" {
  capabilities = [ "create", "read", "update", "delete", "list", "sudo" ]
}
```
```
vault policy write pki-admin pki_admin.policy
export VAULT_TOKEN=$(vault token create -policy pki-admin -format json |jq -r ".auth.client_token")

vault secrets enable pki
vault secrets tune -max-lease-ttl=8760h pki
vault write -field=certificate pki/root/generate/internal common_name="Netology DevOps-7 Root CA" ttl=8760h >ca_cert.crt
vault write pki/config/urls \
	issuing_certificates="http://172.28.128.10:8200/v1/pki/ca" \
	crl_distribution_points="http://172.28.128.10:8200/v1/pki/crl"

vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=4380h pki_int
vault write -format=json pki_int/intermediate/generate/internal \
	common_name="Netology DevOps-7 Intermediate Authority" \
	| jq -r '.data.csr' > pki_intermediate.csr
vault write -format=json pki/root/sign-intermediate csr=@pki_intermediate.csr format=pem_bundle ttl="4380h" \
	| jq -r '.data.certificate' > intermediate.cert.pem

vault write pki_int/intermediate/set-signed certificate=@intermediate.cert.pem

vault write pki_int/roles/pki-issuer allowed_domains="example.com" allow_subdomains=true max_ttl="720h"
```
Получились сертификатики:
```
$ for cert in ca_cert.crt intermediate.cert.pem ; do openssl x509 -noout -dates -subject -in $cert; done
notBefore=May 17 00:29:17 2021 GMT
notAfter=May 17 00:29:46 2022 GMT
subject=CN = Netology DevOps-7 Root CA

notBefore=May 17 00:29:49 2021 GMT
notAfter=Nov 15 12:30:19 2021 GMT
subject=CN = Netology DevOps-7 Intermediate Authority
```

---
> 4. Согласно этой же инструкции, подпишите Intermediate CA csr на сертификат для тестового домена (например, `netology.example.com` если действовали согласно инструкции).

```
$ vault write pki_int/issue/pki-issuer common_name="netology.example.com" ttl="240h"

notBefore=May 17 00:35:44 2021 GMT
notAfter=May 27 00:36:14 2021 GMT
subject= /CN=netology.example.com
```
---

> 5. Поднимите на localhost nginx, сконфигурируйте default vhost для использования подписанного Vault Intermediate CA сертификата и выбранного вами домена. 
> Сертификат из Vault подложить в nginx руками.

В `/etc/ssl/certs/netology.example.com.cert.pem` запишем цепочку сертификатов - собственно, сам сертификат и Intermediate, который его подписал.<br> 
В `/etc/ssl/private/netology.example.com.key.pem` запишем приватный ключ сертификата, и установим на него права: `chmod 600`.<br>
В `/etc/nginx/sites-available/default` добавим: 
```
listen 443 ssl default_server;
listen [::]:443 ssl default_server;
ssl_certificate /etc/ssl/certs/netology.example.com.cert.pem;
ssl_certificate_key /etc/ssl/private/netology.example.com.key.pem;
server_name netology.example.com;
```
И релоаднем nginx.

---
> 6. Модифицировав `/etc/hosts` и [системный trust-store](http://manpages.ubuntu.com/manpages/focal/en/man8/update-ca-certificates.8.html), добейтесь безошибочной с точки зрения HTTPS работы curl на ваш тестовый домен (отдающийся с localhost). Рекомендуется добавлять в доверенные сертификаты Intermediate CA. Root CA добавить было бы правильнее, но тогда при конфигурации nginx потребуется включить в цепочку Intermediate, что выходит за рамки лекции.

Звучит как вызов :) Ну, так как мы на сервер с nginx записали цепочку сертификатов c Intermediate, мы вполне можем добавить наш корневой сертификат.
Запишем его на клиентский хост в `/usr/local/share/ca-certificates/netology-devops7-ca.crt`, и выполним команду `update-ca-certificates`.
И добавим запись в `/etc/hosts`:
```
172.28.128.20 netology.example.com
```
Попробуем, как это работает:
```
# curl https://netology.example.com
<!DOCTYPE html>
<html>
<head>
<title>Welcome to NETOLOGY.EXAMPLE.COM!</title>
...
```
ура, хорошо работает.

---

> 7. [Ознакомьтесь](https://letsencrypt.org/ru/docs/client-options/) с протоколом ACME и CA Let's encrypt. Если у вас есть во владении доменное имя с платным TLS-сертификатом, который возможно заменить на LE, или же без HTTPS вообще, попробуйте воспользоваться одним из предложенных клиентов, чтобы сделать веб-сайт безопасным (или перестать платить за коммерческий сертификат).

Делал тут намедни для одного хоста с множеством имён, с аутентификацией через webroot.
```
# cat /etc/nginx/default.d/certbot.conf
location /.well-known/ {
	root /var/certs;
}

# cat /etc/letsencrypt/cli.ini
authenticator = webroot
webroot-path = /var/certs
deploy-hook = nginx -t 2>&1 && systemctl reload nginx
text = True
allow-subset-of-names = True
```

Регистрируемся:
```
# certbot register --email admins@example.com
```

И получаем сертификат на все наши многочисленные доменные имена:
```
# certbot certonly -n --keep-until-expiring --cert-name examplecom \
   $(cat /etc/nginx/conf.d/examplecom-hostnames.inc |grep -Ev '^(server_name|;)' |sed -e 's/^/-d /' |tr '\n' ' ')
```
---

> **Дополнительное задание вне зачета.** Вместо ручного подкладывания сертификата в nginx, воспользуйтесь [consul-template](https://medium.com/hashicorp-engineering/pki-as-a-service-with-hashicorp-vault-a8d075ece9a) для автоматического подтягивания сертификата из Vault.

Сделаем ещё одну роль для генерации краткосрочных автоматически подтягиваемых сертификатов:
```
vault write pki_int/roles/pki-issuer2 allowed_domains="example.com" allow_subdomains=true max_ttl="2m" generate_lease=true
```

Возьмём из той инструкции политику для PKI-клиента:
```hcl
path "pki_int/issue/*" {
	capabilities = ["create", "update"]
}

path "pki_int/certs" {
	capabilities = ["list"]
}

path "pki_int/revoke" {
	capabilities = ["create", "update"]
}

path "pki_int/tidy" {
	capabilities = ["create", "update"]
}

path "pki/cert/ca" {
	capabilities = ["read"]
}

path "auth/token/renew" {
	capabilities = ["update"]
}

path "auth/token/renew-self" {
	capabilities = ["update"]
}
```

И сделаем для `consul-template` токен на её основе:
```
$ vault token create -policy pki-admin -format json |jq -r ".auth.client_token"
s.R5J2nvgHKUe2vq5MHJqTXzPg
```

Теперь поставим на хост с nginx `consul-template`, сделаем для него юнит-файл, 
и напишем конфигурацию с шаблонами (выдавать сертификат мы будем на отдельный 
домен `netology1.example.com`):
```
# cat /etc/systemd/system/consul-template.service
[Unit]
Description=consul-template
Requires=network-online.target
After=network-online.target

[Service]
Restart=on-failure
ExecStart=/usr/local/bin/consul-template -config='/etc/consul-template.d/pki_netology.hcl'
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```
```hcl
# /etc/consul-template.d/pki_netology.hcl
vault {
  address = "http://172.28.128.10:8200"
  token = "s.R5J2nvgHKUe2vq5MHJqTXzPg"
  renew_token = true
  
  retry {
    enabled = true
    attempts = 5
    backoff = "250ms"
  }
}

template {
  source      = "/etc/consul-template.d/netology-cert.tpl"
  destination = "/etc/ssl/certs/netology1.example.com.cert.pem"
  perms       = "0644"
  command     = "systemctl reload nginx"
}

template {
  source      = "/etc/consul-template.d/netology-key.tpl"
  destination = "/etc/ssl/private/netology1.example.com.key.pem"
  perms       = "0600"
  command     = "systemctl reload nginx"
}
```

```
# cat /etc/consul-template.d/netology-cert.tpl
{{- /* netology-cert.tpl */ -}}
{{ with secret "pki_int/issue/pki-issuer2" "common_name=netology1.example.com"  "ttl=2m" }}
{{ .Data.certificate }}
{{ .Data.issuing_ca }}{{ end }}

# cat /etc/consul-template.d/netology-key.tpl
{{- /* netology-key.tpl */ -}}
{{ with secret "pki_int/issue/pki-issuer2" "common_name=netology1.example.com" "ttl=2m"}}
{{ .Data.private_key }}{{ end }}
```

Попробуем, как это работает:
```
consul-template -config='/etc/consul-template.d/pki_netology.hcl'
^CCleaning up...
```
Несмотря на зловещее молчание в консоли, сертификаты с ключом подтянулись! Ууу, магия. 
```
# openssl x509 -in /etc/ssl/certs/netology1.example.com.cert.pem -noout -subject -dates
subject=CN = netology1.example.com
notBefore=May 18 00:58:45 2021 GMT
notAfter=May 18 01:01:15 2021 GMT
```
Правда, выдаётся на немного побольше, чем на 2 минуты. 30 секунд в подарок.

Ок, настроим и релоаднем nginx:
```
# cat /etc/nginx/sites-enabled/netology1 
server {
	listen 443 ssl;
	listen [::]:443 ssl;
	server_name netology1.example.com;
	ssl_certificate /etc/ssl/certs/netology1.example.com.cert.pem;
	ssl_certificate_key /etc/ssl/private/netology1.example.com.key.pem;
	root /var/www/netology1;
	index index.html;
}
```

На клиенте добавим в /etc/hosts ещё и `netology1.example.com`... ии... пробуем...
```
# curl https://netology1.example.com
curl: (60) SSL certificate problem: certificate has expired
```
Упс, забыли сервис `consul-template` запустить! А пока настраивали nginx, тестово полученный сертификат уже проэкпирился, TTL 2 минуты ж только.

Ок, запускаем сервис, пробуем снова...
```
# curl https://netology1.example.com
<!DOCTYPE html>
<html>
<head>
<title>This is NETOLOGY1.EXAMPLE.COM!</title>
...
```
Вот теперь всё хорошо :)