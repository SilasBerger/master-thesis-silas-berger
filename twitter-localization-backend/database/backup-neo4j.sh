docker-compose down
echo "Backup :: Enter archive name: "
read ARCHIVE_NAME
docker run --rm -v database_neo4j_data:/data -v $(pwd):/backup ubuntu tar cvf /backup/${ARCHIVE_NAME}.tar /data
docker-compose up -d