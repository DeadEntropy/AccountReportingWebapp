docker login
docker build --no-cache -t thermal_control.
docker tag thermal_control deadentropy/thermal_control:latest
docker push deadentropy/thermal_control:latest
