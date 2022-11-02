#!/bin/sh

if [ "$#" -ne 1 ];
then
  echo
  echo "Usage: $0 target_address:port"
  echo
  echo "target_address is the hostname or IP address of the system that runs pcm-sensor-server"
  exit 1
fi

sed "s#PCMSENSORSERVER#$1#g" prometheus.yml.template > prometheus.yml

mkdir -p grafana_volume/dashboards
mkdir -p prometheus_volume

chmod -R 777 *_volume

mkdir -p provisioning/datasources
cp automatic_prometheus.yml provisioning/datasources/automatic.yml 

echo Downloading PCM dashboard
curl -o grafana_volume/dashboards/pcm-dashboard.json $1/dashboard/prometheus

echo Creating prometheus-grafana pod
podman pod create --name prometheus-grafana -p 9090:9090 -p 3000:3000
echo Starting prometheus
podman run --name prometheus -d --pod prometheus-grafana -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml -v $PWD/prometheus_volume:/prometheus prom/prometheus
echo Starting grafana
podman run -d --name grafana --pod prometheus-grafana -v $PWD/grafana_volume:/var/lib/grafana -v $PWD/provisioning:/etc/grafana/provisioning grafana/grafana

echo Start browser at http://localhost:3000/ and login with admin user, password admin


