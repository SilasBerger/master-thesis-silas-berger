docker-compose down
echo "Restore :: Enter archive name: "
read ARCHIVE_NAME
docker volume rm database_mongodb_data
docker-compose up -d
docker-compose down
docker run --rm -v database_mongodb_data:/data/db -v $(pwd):/backup ubuntu bash -c "cd /data/db && tar xvf /backup/${ARCHIVE_NAME}.tar --strip 2"
docker-compose up -d