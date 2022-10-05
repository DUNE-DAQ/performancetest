podman pod rm prometheus-grafana

for c in grafana telegraf influxdb prometheus; do

	id=`podman ps -a -q --filter="name=$c" --format="{{.ID}}"`
	if [ ! -z "$id" ]
	then
	   echo Stopping and deleting $c
	   podman rm $(podman stop $id)
	fi
done

