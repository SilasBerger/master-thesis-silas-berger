docker-compose down
echo "Backup :: Enter archive name: "
read ARCHIVE_NAME
docker run --rm -v database_mongodb_data:/data/db -v $(pwd):/backup ubuntu tar cvf /backup/${ARCHIVE_NAME}.tar /data/db
docker-compose up -d