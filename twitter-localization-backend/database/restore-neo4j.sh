docker-compose down
echo "Restore :: Enter archive name: "
read ARCHIVE_NAME
docker volume rm database_neo4j_data
docker-compose up -d
docker-compose down
docker run --rm -v database_neo4j_data:/data -v $(pwd):/backup ubuntu bash -c "cd /data && tar xvf /backup/${ARCHIVE_NAME}.tar --strip 1"
docker-compose up -d