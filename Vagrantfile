# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/xenial64"

  config.vm.define "pandas-drf-tools-test-vm" do |vm_define|
  end

  config.vm.hostname = "pandas-drf-tools-test.local"

  config.vm.network "forwarded_port", guest: 80, host: 8000
  config.vm.network "forwarded_port", guest: 8000, host: 8001

  config.vm.synced_folder ".", "/home/ubuntu/pandas_drf_tools_test/"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
    vb.cpus = 1
    vb.name = "pandas-drf-tools-test"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y nginx git build-essential python3 python3.5-venv python3-dev
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    pyvenv-3.5 --without-pip pandas_drf_tools_test_venv
    source pandas_drf_tools_test_venv/bin/activate
    curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | python

    pip install Cython
    pip install -r pandas_drf_tools_test/requirements.txt

    cd pandas_drf_tools_test/pandas_drf_tools_test/

    python manage.py migrate
    python manage.py download_census_data
    python manage.py collectstatic --noinput
  SHELL

  config.vm.provision "shell", inline: <<-SHELL
    echo '
upstream pandas_drf_tools_test_upstream {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 4G;

    access_log /home/ubuntu/pandas_drf_tools_test/nginx_access.log;
    error_log /home/ubuntu/pandas_drf_tools_test/nginx_error.log;

    location /static/ {
        alias /home/ubuntu/pandas_drf_tools_test/pandas_drf_tools_test/static/;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        if (!-f $request_filename) {
            proxy_pass http://pandas_drf_tools_test_upstream;
            break;
        }
    }
}
    ' > /etc/nginx/conf.d/pandas_drf_tools_test.conf

    /usr/sbin/service nginx restart
  SHELL

  config.vm.provision "shell", run: "always", privileged: false, inline: <<-SHELL
    source /home/ubuntu/pandas_drf_tools_test_venv/bin/activate
    cd /home/ubuntu/pandas_drf_tools_test/pandas_drf_tools_test
    gunicorn --bind 127.0.0.1:8000 --daemon --workers 1 pandas_drf_tools_test.wsgi
  SHELL
end
